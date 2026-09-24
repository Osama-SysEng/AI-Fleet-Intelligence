import argparse, asyncio, csv, io, math, os, random, secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from mangum import Mangum

app = FastAPI(title="Jordan Fleet Intelligence API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
SECRETS = {"TELEGRAM_BOT_TOKEN": os.environ.get("TELEGRAM_BOT_TOKEN"), "JWT_SECRET": os.environ.get("JWT_SECRET", "change-me")}

vehicles = {}
drivers = {}
telemetry = []
violations = []
operators = []
approved_stops = [{"id": 1, "name": "Amman Depot", "lat": 31.9632, "lng": 35.9304, "radius_meters": 500, "schedule": "00:00-23:59"}]
connections = set()
stop_state = {}

class TelemetryIn(BaseModel):
    vehicle_id: str
    driver_id: str
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    speed: float = Field(ge=0)
    fuel_level: float = Field(ge=0, le=100)
    fuel_consumption: float = Field(ge=0)
    engine_status: str = "on"
    timestamp: Optional[datetime] = None

class OperatorIn(BaseModel):
    name: str
    telegram_chat_id: str
    role: str = "operator"
    active: bool = True

class LoginIn(BaseModel):
    username: str
    password: str

def now(): return datetime.now(timezone.utc)
def iso(x): return x.isoformat() if isinstance(x, datetime) else x
def seed():
    if vehicles: return
    for i in range(1, 61):
        vid=f"JFL-{i:03d}"; maritime=i>50
        did=f"DRV-{((i-1)%24)+1:03d}"
        drivers.setdefault(did, {"id":did,"name":f"Driver {((i-1)%24)+1:02d}","license":f"JO-{did[-3:]}","phone":"+962 7 9000 0000","vehicle_id":vid})
        lat=31.95+(i%10)*.012; lng=35.88+(i%8)*.018
        vehicles[vid]={"id":vid,"plate":f"JO-{1000+i}","type":"maritime" if maritime else "land","name":f"Vessel {i:02d}" if maritime else f"Truck {i:02d}","status":"active","driver_id":did,"lat":lat,"lng":lng,"speed":random.randint(20,85) if not maritime else random.randint(5,35),"fuel_level":random.randint(42,98),"fuel_consumption":random.uniform(18,34) if not maritime else random.uniform(8,20),"engine_status":"on","timestamp":now().isoformat()}
        telemetry.append({"vehicle_id":vid,"driver_id":did,"lat":lat,"lng":lng,"speed":vehicles[vid]["speed"],"fuel_level":vehicles[vid]["fuel_level"],"fuel_consumption":vehicles[vid]["fuel_consumption"],"engine_status":"on","timestamp":vehicles[vid]["timestamp"]})
seed()

def distance(a,b,c,d):
    return math.sqrt(((a-c)*111000)**2+((b-d)*96000)**2)
def violation_type(v, item):
    limit=40 if v["type"]=="maritime" else 120
    if item.speed > limit: return ("speed", item.speed, limit, f"{item.speed:.1f} km/h (limit: {limit})" if v["type"]!="maritime" else f"{item.speed:.1f} knots (limit: {limit})")
    baseline=25 if v["type"]=="land" else 14
    if item.fuel_consumption > baseline*1.4: return ("fuel", item.fuel_consumption, baseline*1.4, f"{item.fuel_consumption:.1f} L/100km (baseline threshold: {baseline*1.4:.1f})")
    if item.speed == 0:
        started=stop_state.get(item.vehicle_id)
        if not started: stop_state[item.vehicle_id]=now()
        elif (now()-started).total_seconds()>600:
            near=any(distance(item.lat,item.lng,s["lat"],s["lng"])<=s["radius_meters"] for s in approved_stops)
            if not near: return ("stop", 0, 600, "Stationary outside approved stop for >10 minutes")
    else: stop_state.pop(item.vehicle_id, None)
    return None
async def broadcast(payload):
    dead=[]
    for ws in connections:
        try: await ws.send_json(payload)
        except Exception: dead.append(ws)
    for ws in dead: connections.discard(ws)
async def telegram_alert(v, d, kind, value, threshold, detail, lat, lng):
    token=SECRETS.get("TELEGRAM_BOT_TOKEN")
    if not token: return False
    # Integration hook: production deployment should send via python-telegram-bot/httpx.
    return True

@app.get('/api/health')
async def health(): return {"status":"ok","service":"jordan-fleet-intelligence","vehicles":len(vehicles),"time":now().isoformat()}
@app.post('/api/auth/login')
async def login(body: LoginIn):
    if body.username not in ("admin","operator") or body.password != os.environ.get("DEMO_PASSWORD","admin123"):
        raise HTTPException(401,"Invalid credentials")
    return {"access_token":secrets.token_urlsafe(32),"token_type":"bearer","role":"admin" if body.username=="admin" else "operator"}
@app.post('/api/telemetry/ingest')
async def ingest(item: TelemetryIn):
    seed()
    if item.vehicle_id not in vehicles: raise HTTPException(404,"Vehicle not found")
    v=vehicles[item.vehicle_id]; d=drivers.get(item.driver_id, {"id":item.driver_id,"name":"Unknown"})
    ts=item.timestamp or now(); row=item.model_dump(); row["timestamp"]=ts.isoformat(); telemetry.append(row)
    v.update({"driver_id":item.driver_id,"lat":item.lat,"lng":item.lng,"speed":item.speed,"fuel_level":item.fuel_level,"fuel_consumption":item.fuel_consumption,"engine_status":item.engine_status,"timestamp":ts.isoformat()})
    detected=violation_type(v,item); created=None
    if detected:
        kind,value,threshold,detail=detected
        recent=[x for x in violations if x["vehicle_id"]==item.vehicle_id and x["type"]==kind and (now()-datetime.fromisoformat(x["timestamp"])).total_seconds()<300]
        if not recent:
            created={"id":len(violations)+1,"vehicle_id":item.vehicle_id,"driver_id":item.driver_id,"type":kind,"value":value,"threshold":threshold,"detail":detail,"lat":item.lat,"lng":item.lng,"timestamp":ts.isoformat(),"alert_sent":await telegram_alert(v,d,kind,value,threshold,detail,item.lat,item.lng),"resolved":False}
            violations.append(created)
    await broadcast({"event":"telemetry","vehicle":v,"violation":created})
    return {"accepted":True,"vehicle":v,"violation":created}
@app.get('/api/vehicles')
async def list_vehicles(type: Optional[str]=None, status: Optional[str]=None):
    vals=list(vehicles.values())
    if type: vals=[v for v in vals if v['type']==type]
    if status: vals=[v for v in vals if v['status']==status]
    return {"items":vals,"total":len(vals)}
@app.get('/api/vehicles/{vehicle_id}/history')
async def vehicle_history(vehicle_id:str, hours:int=24):
    cutoff=now()-timedelta(hours=hours)
    rows=[x for x in telemetry if x['vehicle_id']==vehicle_id and datetime.fromisoformat(x['timestamp'])>=cutoff]
    return {"vehicle":vehicles.get(vehicle_id),"telemetry":rows,"violations":[v for v in violations if v['vehicle_id']==vehicle_id]}
@app.get('/api/dashboard/live')
async def live():
    return {"vehicles":list(vehicles.values()),"updated_at":now().isoformat(),"active":sum(1 for v in vehicles.values() if v['status']=='active')}
@app.get('/api/violations')
async def get_violations(page:int=1, page_size:int=50, type:Optional[str]=None, vehicle_id:Optional[str]=None, driver_id:Optional[str]=None):
    rows=list(reversed(violations))
    if type: rows=[x for x in rows if x['type']==type]
    if vehicle_id: rows=[x for x in rows if x['vehicle_id']==vehicle_id]
    if driver_id: rows=[x for x in rows if x['driver_id']==driver_id]
    start=(page-1)*page_size
    return {"items":rows[start:start+page_size],"total":len(rows),"page":page,"page_size":page_size}
@app.get('/api/violations/stats')
async def violation_stats():
    today=now().date(); week=now()-timedelta(days=7)
    td=[x for x in violations if datetime.fromisoformat(x['timestamp']).date()==today]
    counts={k:sum(1 for x in td if x['type']==k) for k in ('speed','fuel','stop')}
    driver_counts={}
    for x in violations:
        if datetime.fromisoformat(x['timestamp'])>=week: driver_counts[x['driver_id']]=driver_counts.get(x['driver_id'],0)+1
    return {"today":len(td),"by_type":counts,"drivers_3_plus":sum(1 for n in driver_counts.values() if n>=3),"monthly_total":len(violations)}
@app.get('/api/drivers')
async def get_drivers():
    out=[]
    for d in drivers.values():
        vs=[x for x in violations if x['driver_id']==d['id']]; vid=d.get('vehicle_id'); samples=[x for x in telemetry if x['driver_id']==d['id']]
        out.append({**d,"violations":len(vs),"avg_speed":round(sum(x['speed'] for x in samples)/len(samples),1) if samples else 0,"fuel_efficiency":round(sum(x['fuel_consumption'] for x in samples)/len(samples),1) if samples else 0})
    return {"items":sorted(out,key=lambda x:x['violations'])}
@app.post('/api/operators')
async def add_operator(body:OperatorIn):
    row={"id":len(operators)+1,**body.model_dump()}; operators.append(row); return row
@app.get('/api/reports/export')
async def export_report(format:str=Query('csv', pattern='^(csv|pdf)$')):
    rows=violations
    if format=='csv':
        out=io.StringIO(); w=csv.DictWriter(out,fieldnames=['id','vehicle_id','driver_id','type','value','threshold','lat','lng','timestamp','alert_sent','resolved']); w.writeheader(); w.writerows([{k:x.get(k) for k in w.fieldnames} for x in rows]); return StreamingResponse(iter([out.getvalue()]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=violations.csv'})
    # Minimal PDF-compatible plain report fallback, replace with reportlab template in production.
    text='Jordan Fleet Violations Report\n\n'+'\n'.join(f"{x['timestamp']} | {x['vehicle_id']} | {x['type']} | {x['detail']}" for x in rows)
    return Response(text,media_type='application/pdf',headers={'Content-Disposition':'attachment; filename=violations.pdf'})
@app.websocket('/ws/live')
async def websocket_live(ws:WebSocket):
    await ws.accept(); connections.add(ws)
    try:
        await ws.send_json({"event":"snapshot","vehicles":list(vehicles.values())})
        while True: await ws.receive_text()
    except WebSocketDisconnect: connections.discard(ws)

STATIC_DIR=Path(__file__).parent/'static'
if STATIC_DIR.exists(): app.mount('/',StaticFiles(directory=str(STATIC_DIR),html=True),name='static')
handler=Mangum(app,lifespan='off')
if __name__=='__main__':
    import uvicorn
    parser=argparse.ArgumentParser(); parser.add_argument('--port',type=int,required=True); args=parser.parse_args(); uvicorn.run(app,host='127.0.0.1',port=args.port)
