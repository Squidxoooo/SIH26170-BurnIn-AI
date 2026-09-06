from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ComponentInput(BaseModel):
    component_id: str
    lot_id: Optional[str] = None
    values: Dict[str, float] = Field(default_factory=dict)
    specification_limit: Optional[float] = None

class AnalysisResult(BaseModel):
    component_id: str
    lot_id: Optional[str]
    static_check: Dict[str, Any]
    anomaly_analysis: Dict[str, Any]
    drift_prediction: Dict[str, Any]
    drift_analysis: Dict[str, Any]
    risk: Dict[str, Any]
    decision: str
    explanation: List[str]
    model_metadata: Dict[str, Any]
