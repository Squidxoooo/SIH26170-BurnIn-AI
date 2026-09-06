from fastapi import APIRouter
router = APIRouter()
@router.post("/anomaly/detect")
def anomaly_detect(payload: dict):
    return {"success": False, "error":{"code":"MODEL_NOT_LOADED","message":"Train/load the anomaly model before inference."}}
