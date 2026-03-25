# FARMZY - AI Expert System for Smart Irrigation and Crop Intelligence

This repository includes an end-to-end FARMZY scaffold:

- `supabase/schema.sql`: full PostgreSQL schema, RLS, views, trigger, publication, and seed data.
- `farmzy-backend/`: FastAPI backend with ThingSpeak ingestion, rule engine, fuzzy logic, ML services, scheduler, REST APIs, and WebSocket streaming.
- `farmzy-frontend/`: Next.js 14 dashboard with realtime pages/components and API integration.
- `ml-pipeline/`: standalone model training pipeline exporting `.joblib` artifacts.
- `hardware/farmzy_esp32.ino`: ESP32 firmware with simulation mode and ThingSpeak upload.
- `docs/AI_Expert_System_Design.md`: academic chapter draft.

## Recommended Order

1. Run `ml-pipeline/train_pipeline.py` and copy artifacts to `farmzy-backend/ml/artifacts/`.
2. Execute `supabase/schema.sql` in Supabase SQL editor.
3. Start backend from `farmzy-backend/`.
4. Start frontend from `farmzy-frontend/`.
5. Flash `hardware/farmzy_esp32.ino` with `SIMULATION_MODE` enabled.
