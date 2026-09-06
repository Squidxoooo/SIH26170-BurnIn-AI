from fastapi import FastAPI
from backend.api.routes.health import router as health_router
from backend.api.routes.analysis import router as analysis_router
from backend.api.routes.prediction import router as prediction_router
from backend.api.routes.anomaly import router as anomaly_router
from backend.api.routes.components import router as components_router
from backend.api.routes.lots import router as lots_router

app = FastAPI(title="AI Burn-In Reliability Screening API", version="1.0.0")
for r in [health_router, analysis_router, prediction_router, anomaly_router, components_router, lots_router]:
    app.include_router(r, prefix="/api/v1")
