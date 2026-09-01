import React, { useEffect, useState } from "react";
import { Map, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { useSelector, useDispatch } from "react-redux";
import { Chart, Line } from "react-chartjs-2";
import { Button, Card, CardTitle, CardContent, Grid } from "reactstrap";
import { setVehicles, setViolations, setKPIs } from "../redux/store";
import io from "socket.io-client";

function Dashboard() {
  const dispatch = useDispatch();
  
  // Redux state
  const vehicles = useSelector((state) => state.vehicles || []);
  const violations = useSelector((state) => state.violations || []);
  const kpis = useSelector((state) => state.kpis || {});
  const socket = useSelector((state) => state.socket || null);
  
  // Socket.io connection for real-time updates
  useEffect(() => {
    const socketUrl = "http://localhost:8000";
    const newSocket = io(socketUrl);
    
    newSocket.on("vehicle_update", (vehicle) => {
      dispatch(setVehicles(vehicle));
    });
    
    newSocket.on("violation_detected", (violation) => {
      dispatch(setViolations(violation));
    });
    
    newSocket.on("kpi_update", (kpis) => {
      dispatch(setKPIs(kpis));
    });
    
    return () => newSocket.disconnect();
  }, [dispatch]);
  
  // KPI cards
  const { totalVehicles, activeViolations, fleetEfficiency, fuelSaved } = kpis;
  
  return (
    <div style={{ height: "100vh", fontFamily: "Arial, sans-serif" }}>
      <header style={{ 
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        color: "white", padding: "1rem", margin: "-1rem -1rem 2rem -1rem"
      }}>
        <h1 style={{ margin: 0, fontSize: "1.5rem" }}>
          Jordan Fleet Intelligence Dashboard
        </h1>
      </header>
      
      <main style={{ padding: "0 1rem 2rem 1rem" }}>
        <Grid>
          {/* KPI Cards Row */}
          <Card style={{ marginBottom: "1rem", borderRadius: "8px" }}>
            <CardTitle>Fleet Overview</CardTitle>
            <CardContent>
              <Grid>
                <Grid col={4} style={{ textAlign: "center", marginBottom: "1rem" }}>
                  <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#667eea" }}>
                    {totalVehicles || 0}
                  </div>
                  <div>Total Vehicles</div>
                </Grid>
                <Grid col={4} style={{ textAlign: "center", marginBottom: "1rem" }}>
                  <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#f72585" }}>
                    {activeViolations || 0}
                  </div>
                  <div>Active Violations</div>
                </Grid>
                <Grid col={4} style={{ textAlign: "center", marginBottom: "1rem" }}>
                  <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#4facfe" }}>
                    {fleetEfficiency || "0%"}
                  </div>
                  <div>Fleet Efficiency</div>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
          
          {/* Fuel Saved Card */}
          <Card style={{ marginBottom: "1rem", borderRadius: "8px" }}>
            <CardTitle>Fuel Saved</CardTitle>
            <CardContent>
              <div style={{ fontSize: "2rem", fontWeight: "bold", color: "#43e97b" }}>
                {(fuelSaved || 0):.1f}
              </div>
              <div>Liters Saved This Month</div>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Map Section */}
        <section style={{ marginTop: "2rem", height: "400px", borderRadius: "8px", overflow: "hidden" }}>
          <h2 style={{ marginBottom: "1rem", color: "#333" }}>Live Vehicle Tracking</h2>
          <Map style={{ height: "100%", width: "100%" }} center={[-3.47, 36.82]} zoom={6}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution="Copyright &copy; OpenStreetMap contributors"
            />
            {vehicles.map((vehicle) => (
              <Marker key={vehicle.vehicle_id} position={[vehicle.gps_lat, vehicle.gps_lng]}>
                <Popup>
                  <strong>{vehicle.plate_number}</strong><br/>
                  {vehicle.vehicle_type}<br/>
                  Speed: {vehicle.speed} km/h<br/>
                  Fuel: {vehicle.fuel_level}%
                </Popup>
              </Marker>
            ))}
          </Map>
        </section>
        
        {/* Violations Section */}
        <section style={{ marginTop: "2rem" }}>
          <h2 style={{ marginBottom: "1rem", color: "#333" }}>Active Violations</h2>
          {violations.length === 0 ? (
            <p style={{ color: "#666" }}>No active violations</p>
          ) : (
            <ul style={{ listStyle: "none", padding: 0 }}>
              {violations.map((violation) => (
                <li key={violation.id} style={{ 
                  borderLeft: "3px solid #ff0000", padding: "0.5rem 0", margin: "0.5rem 0"
                }}>
                  <strong>{violation.vehicle.plate_number}</strong> - 
                  {violation.violation_type.replace("_", " ")}<br/>
                  <small>{violation.timestamp}</small>
                </li>
              ))}
            </ul>
          )}
        </section>
        
        {/* Charts Section */}
        <section style={{ marginTop: "2rem", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "2rem" }}>
          {/* Speed Trend Chart */}
          <Card>
            <CardTitle>Speed Trends (Last 24h)</CardTitle>
            <CardContent>
              <Chart 
                data={{
                  labels: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                  datasets: [
                    {
                      label: "Avg Speed (km/h)",
                      data: [60, 75, 85, 90, 70, 55],
                      borderColor: "#667eea",
                      backgroundColor: "#667eea30",
                      fill: true,
                    }
                  ]
                }}
                options={{ responsive: true }}
              />
            </CardContent>
          </Card>
          
          {/* Violation Frequency Chart */}
          <Card>
            <CardTitle>Violation Frequency</CardTitle>
            <CardContent>
              <Chart
                data={{
                  labels: ["Speed", "Fuel", "Unauthorized Stop"],
                  datasets: [
                    {
                      label: "Violations Count",
                      data: [
                        violations.filter(v => v.violation_type === "speed_breach").length,
                        violations.filter(v => v.violation_type === "fuel_waste").length,
                        violations.filter(v => v.violation_type === "unauthorized_stop").length,
                      ],
                      backgroundColor: ["#ff5f57", "#4facfe", "#43e97b"],
                    }
                  ]
                }}
                options={{ responsive: true }}
              />
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}

export default Dashboard;
