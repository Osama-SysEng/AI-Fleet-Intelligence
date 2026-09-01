# AI Fleet Intelligence — Jordan Fleet Simulation

هذا الأرشيف هو نواة محاكاة آمنة لتحليلات أسطول المركبات. يدعم استقبال Telemetry متحققًا، منع التكرار، تحليلًا تفسيريًا لثلاثة أنواع من المخالفات، تخزين PostgreSQL اختياريًا، ولوحة مراقبة محلية. لا يرسل Telegram، ولا ينفذ Dispatch، ولا يتحكم في مركبة.

## التشغيل المحلي

انسخ `backend/.env.example` إلى `backend/.env`، غيّر `POSTGRES_PASSWORD` و`OPERATOR_TOKENS` إلى قيم عشوائية محلية، ثم شغّل:

```bash
docker compose --env-file backend/.env -f docker/docker-compose.yml up --build
```

تتوفر الواجهة على `http://localhost:8080` والـAPI على `http://localhost:8000`. لا تنشر منفذ PostgreSQL خارج شبكة Compose. في بيئة الإنتاج يجب استخدام مدير أسرار، TLS، RBAC، سجلات مركزية، نسخ احتياطية واختبارات استعادة.

## API

يرسل `POST /api/v1/telemetry` كائنًا يحتوي على `vehicle_id` و`sequence` و`occurred_at` مع timezone و`latitude` و`longitude` و`speed_kph` و`fuel_percent` و`engine_temp_c`. تستخدم القراءة مرة واحدة لكل زوج `vehicle_id:sequence`، وتُرفض القيم الخارجة عن الحدود. تتطلب مسارات `/events` و`/audit` ترويسة `X-Operator-Token` عند إعداد الرموز.

## الاختبارات

```bash
python3 -m unittest discover -s backend/tests -p 'test_*.py'
python3 -m compileall -q backend
```

## الأمان وحدود الاستخدام

الموقع المعروض تقريبي وليس سياسة خصوصية مكتملة. يجب تشفير الموقع والهوية في التخزين، تطبيق عزل tenant، سياسة احتفاظ، ومراجعة قانونية قبل التشغيل الحقيقي. توصيات المخالفات لا تُستخدم وحدها في قرارات تأديبية أو توظيف أو صيانة ميدانية. يتطلب أي ربط فعلي بمركبات أو Telegram تصميم موصل مستقل، اعتمادًا وموافقة، اختبار staging، وسجل تدقيق.
