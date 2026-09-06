from fastapi import APIRouter, HTTPException
from backend.data.dataset_repository import DatasetRepository
router = APIRouter()
repository = DatasetRepository()
@router.get("/lots/{lot_id}")
def lot(lot_id: str):
    result = repository.lot(lot_id)
    if result is None:
        raise HTTPException(404, "Lot not found in the SIH26170 serving dataset")
    return {"success": True, "data": result}
