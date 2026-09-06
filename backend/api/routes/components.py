from fastapi import APIRouter, HTTPException
from app.data.dataset_repository import DatasetRepository
router = APIRouter()
repository = DatasetRepository()
@router.get("/components/{component_id}")
def component(component_id: str):
    result = repository.component(component_id)
    if result is None:
        raise HTTPException(404, "Component not found in the SIH26170 serving dataset")
    return {"success": True, "data": result}
