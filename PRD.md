# PRD — AI-Fleet-Intelligence (Jordan Fleet Simulation)
## 1. نظرة عامة
- نواة محاكاة آمنة لتحليلات أسطول المركبات (الأردن).
- استقبال Telemetry متحقق + منع تكرار `vehicle_id:sequence`.
- محرك مخالفات تفسيري: سرعة/وقود/حرارة مع `requires_review=true`.
- Backend: FastAPI (`backend/app/main.py` + `app/api/router.py`).
- الواجهة الفعلية: `dashboard/index.html` فقط.
## 2. المستخدمون
1. مرسِل محاكاة (بدون auth) يرسل telemetry يدويًا.
2. مشغّل (operator) يقرأ `/events` و`/audit` عبر `X-Operator-Token`.
3. مدقق يراجع سجل audit للمحاكاة.
## 3. الميزات الأساسية (قابلة للاختبار)
1. قبول `POST /telemetry` متحقق وإرجاع 202 مع حدث.
2. رفض القيم الخارجة عن الحدود (سرعة 0–260، وقود 0–100، حرارة -40–180) بـ400.
3. رفض الإحداثيات غير WGS84 و`occurred_at` بدون timezone بـ400.
4. منع التكرار لكل زوج `vehicle_id:sequence` (عامل واحد `--workers 1`).
5. إرفاق `violations` تفسيرية (سرعة/وقود/حرارة) لكل حدث.
6. قراءة `/events` بحد `limit` من 1 إلى 500 (operator).
7. قراءة `/audit` بحد `limit` من 1 إلى 500 (operator).
8. رفض `/commands` دائمًا بـ409 (حظر سياسة).
9. فحص `/health` يعيد `simulation-only` + حد معدل + ترويسات أمان + CORS مقيد.
## 4. الـAPI endpoints الحقيقية (من الكود فقط)
- `POST /api/v1/telemetry` — status 202.
- `GET /api/v1/events?limit=` — يتطلب `X-Operator-Token` عند ضبطها.
- `GET /api/v1/audit?limit=` — يتطلب `X-Operator-Token` عند ضبطها.
- `POST /api/v1/commands` — يرد 409 دائمًا.
- `GET /health` — `{status:ok, mode:simulation-only, external_dispatch:false, vehicle_control:false}`.
## 5. بيانات الدخول/الإعداد للاختبار
- انسخ `backend/.env.example` إلى `backend/.env`.
- عيّن `OPERATOR_TOKENS=tok-test-1` و`POSTGRES_PASSWORD` عشوائيًا.
- التشغيل: `docker compose --env-file backend/.env -f docker/docker-compose.yml up --build`.
- API: `http://localhost:8000` والواجهة `:8080`. لا تنشر منفذ PostgreSQL.
- الاختبارات: `python3 -m unittest discover -s backend/tests -p 'test_*.py'`.
- مثال صالح: `{vehicle_id, sequence, occurred_at, latitude, longitude, speed_kph, fuel_percent, engine_temp_c}`.
## 6. خارج النطاق (mocked/simulated — صراحة)
- لا إرسال Telegram فعلي (`send` يرفع `RuntimeError`).
- لا Dispatch خارجي ولا أوامر مركبة ولا GPS حي.
- لا اتصال بالمركبات أو CRM أو السائقين — عينات يدوية.
- المخزن in-memory بسقف `MAX_STORE_EVENTS`.
- الموقع تقريبي (منزلتان) وليس بدقة تشغيلية.
- `dashboard/src/Dashboard.js` إرث غير مستخدم (socket.io/redux غائبة).
- التوصيات لا تُستخدم لقرارات تأديبية/توظيف/صيانة.
