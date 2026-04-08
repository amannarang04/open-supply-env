from pydantic import BaseModel, Field
from typing import Optional

class SupplyAction(BaseModel):
    command: str = Field(..., description="Action to take: CHECK_INVENTORY, CHECK_ROUTES, CHECK_ORDERS, REROUTE_ORDER, WAIT")
    order_id: Optional[str] = Field(None, description="Required for REROUTE_ORDER")
    source_warehouse: Optional[str] = Field(None, description="Warehouse_CHI or Warehouse_LA")
    shipping_method: Optional[str] = Field(None, description="GROUND or AIR_FREIGHT")

class SupplyObservation(BaseModel):
    budget_remaining: float
    pending_orders: int
    completed_orders: int
    last_action_feedback: str
    is_done: bool