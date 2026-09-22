# Nagar Drishti — SIH 2026 Prototype

A modular reference implementation for the IRONCLAD / SIH 2026 PS 26124 concept. It covers the judge-facing engineering gaps discussed for the PPT:

- event-driven edge inference
- vehicle tracking
- ANPR with plate detector + OCR
- privacy-first face blurring
- reliable offline buffering and retry/ACK synchronization
- tamper-evident event records (HMAC, not "tamper-proof")
- fleet sensor fusion with spatial/temporal DBSCAN
- expected-vs-observed infrastructure gap detection
- unsafe-driving event heuristics
- road-health scoring
- maintenance priority scoring
- FastAPI backend
- GIS-ready event API
- React + Leaflet command dashboard
- performance/evaluation hooks

> No implementation can guarantee an SIH win. This repository is designed to give you a defensible, demonstrable prototype and concrete evidence for the technical claims in the deck.

## 1. Repository layout

```text
nagar_drishti_sih/
├── edge/
│   ├── config.py
│   ├── schemas.py
│   ├── db.py
│   ├── privacy.py
│   ├── gps.py
│   ├── fusion.py
│   ├── infrastructure.py
│   ├── risk.py
│   ├── road_health.py
│   ├── maintenance.py
│   ├── anpr.py
│   ├── vision.py
│   ├── event_pipeline.py
│   └── sync_client.py
├── backend/app/
│   ├── main.py
│   ├── db.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── services.py
├── dashboard/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       └── styles.css
├── scripts/
│   ├── benchmark_yolo.py
│   ├── run_edge.py
│   └── create_sample_events.py
├── config/config.yaml
├── docs/ARCHITECTURE.md
└── requirements.txt
```

## 2. Edge environment

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Put your actual model weights in `data/models/` and update `config/config.yaml`.

Suggested prototype model roles:

- `road_model`: pothole/crack/waterlogging/road-asset model that YOU have trained/validated.
- `vehicle_model`: vehicle/person model.
- `plate_model`: license-plate detector model.

Do not put a model in the PPT unless you can show its actual measured validation results.

## 3. Backend

```bash
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Health check:

```text
GET http://127.0.0.1:8000/api/health
```

## 4. Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Open the Vite URL shown in the terminal.

The dashboard expects the backend at `http://127.0.0.1:8000` by default.

## 5. Run the edge pipeline

```bash
python scripts/run_edge.py --source 0 --bus-id BUS_17 --config config/config.yaml
```

For a video file:

```bash
python scripts/run_edge.py --source "data/demo.mp4" --bus-id BUS_17 --config config/config.yaml
```

The pipeline creates event records locally, stores evidence paths, applies privacy processing, and queues events for backend synchronization.

## 6. What each module proves to a judge

| Judge concern | Code |
|---|---|
| AI actually integrated | `edge/vision.py` |
| Offline-first | `edge/db.py`, `edge/sync_client.py` |
| Fleet duplicate fusion | `edge/fusion.py` |
| ANPR | `edge/anpr.py` |
| Privacy | `edge/privacy.py` |
| Unsafe driving | `edge/risk.py` |
| Missing infrastructure | `edge/infrastructure.py` |
| Road health | `edge/road_health.py` |
| Maintenance prioritization | `edge/maintenance.py` |
| Backend API | `backend/app/main.py` |
| GIS dashboard | `dashboard/src/App.jsx` |
| Model evaluation | `scripts/benchmark_yolo.py` |
| Tamper-evident records | `backend/app/security.py` |

## 7. Judge-demo flow

```text
Camera frame
   ↓
Edge inference
   ↓
Event JSON + confidence + GPS + timestamp
   ↓
Local persistent queue
   ↓
Internet unavailable? ---- yes ---> keep locally
   |                                   |
   no                                  |
   ↓                                   |
POST /api/events <---------------------+
   ↓
DB + GIS
   ↓
Fusion / Road Health / Maintenance
   ↓
React dashboard
```

## 8. Important claims to keep precise

Use these terms in the PPT and demo:

- "reliable offline buffering" instead of "zero-loss"
- "tamper-evident audit trail" instead of "tamper-proof"
- "suspected vehicle associated with an incident" instead of "offender"
- "potential unsafe-driving event" instead of legal/definitive "rash driving"
- "potential missing infrastructure" instead of claiming absence from a single frame

## 9. What to measure before your final PPT

Run the actual models and record:

- precision
- recall
- mAP50 / mAP50-95 where applicable
- inference FPS
- end-to-end event latency
- ANPR OCR accuracy
- duplicate-fusion rate
- offline replay success rate
- memory/storage usage on edge hardware

Never replace the placeholders in the PPT with invented numbers.
