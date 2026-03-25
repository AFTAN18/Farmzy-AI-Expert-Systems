# FARMZY Backend (FastAPI)

FARMZY backend ingests ThingSpeak IoT data, runs expert-system + fuzzy + ML inference, stores results in Supabase, and streams updates over WebSockets.

## Setup

1. Create and activate Python 3.11+ virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment template and fill secrets:

```bash
cp .env.example .env
```

4. Run backend:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## API Highlights

- `GET /api/farms/{farm_id}/dashboard`
- `GET /api/farms/{farm_id}/readings`
- `GET /api/farms/{farm_id}/predictions`
- `GET /api/farms/{farm_id}/crops`
- `GET /api/farms/{farm_id}/zones`
- `GET /api/farms/{farm_id}/alerts`
- `POST /api/farms/{farm_id}/alerts/{alert_id}/resolve`
- `POST /api/models/retrain`
- `GET /api/models/status`
- `GET /api/expert-system/rules`
- `POST /api/expert-system/rules`
- `PUT /api/expert-system/rules/{rule_id}`
- `GET /api/expert-system/explain/{reading_id}`
- `WS /ws/farm/{farm_id}`

## Manual Retraining

Use the API endpoint:

```bash
curl -X POST http://127.0.0.1:8000/api/models/retrain
```

Or run the training script directly:

```bash
python ml/train.py
```

Artifacts are saved to `ml/artifacts/`.
