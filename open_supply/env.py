import copy
from typing import Tuple, Dict, Any
from open_supply.models import SupplyAction, SupplyObservation

# Data configurations for our tasks
TASKS_CONFIG = {
    "easy_routing": {
        "budget": 1000.0,
        "inventory": {"Warehouse_CHI": 10, "Warehouse_LA": 10},
        "orders": {"ORD-001": {"status": "pending"}}
    },
    "medium_budget": {
        "budget": 150.0, # Tight budget!
        "inventory": {"Warehouse_CHI": 10, "Warehouse_LA": 10},
        "orders": {f"ORD-10{i}": {"status": "pending"} for i in range(1, 4)}
    },
    "hard_optimization": {
        "budget": 300.0,
        "inventory": {"Warehouse_CHI": 2, "Warehouse_LA": 10}, # CHI doesn't have enough for all orders
        "orders": {f"ORD-20{i}": {"status": "pending"} for i in range(1, 6)}
    }
}

# Costs based on routing choices
SHIPPING_COSTS = {"GROUND": 50.0, "AIR_FREIGHT": 200.0}

class OpenSupplyEnv:
    def __init__(self, task_name: str = "easy_routing"):
        if task_name not in TASKS_CONFIG:
            task_name = "easy_routing"
            
        self.task_name = task_name
        self.initial_config = TASKS_CONFIG[self.task_name]
        self.reset()

    def reset(self) -> SupplyObservation:
        # Clone initial state so we can reset cleanly
        self.budget = self.initial_config["budget"]
        self.inventory = copy.deepcopy(self.initial_config["inventory"])
        self.orders = copy.deepcopy(self.initial_config["orders"])
        self.completed = 0
        self.total_orders = len(self.orders)
        self.done = False
        
        return self.state("Environment initialized. Awaiting commands.")

    def state(self, feedback: str = "") -> SupplyObservation:
        pending = sum(1 for o in self.orders.values() if o["status"] == "pending")
        return SupplyObservation(
            budget_remaining=self.budget,
            pending_orders=pending,
            completed_orders=self.completed,
            last_action_feedback=feedback,
            is_done=self.done
        )

    def step(self, action: SupplyAction) -> Tuple[SupplyObservation, float, bool, Dict[str, Any]]:
        if self.done:
            return self.state("Episode already done."), 0.0, True, {"score": self._calculate_score()}

        reward = 0.0
        feedback = ""

        if action.command == "CHECK_INVENTORY":
            feedback = f"Inventory levels: {self.inventory}"
            reward = 0.02  # Small partial reward for gathering info
            
        elif action.command == "CHECK_ORDERS":
            pending = [k for k, v in self.orders.items() if v["status"] == "pending"]
            feedback = f"Pending orders: {pending}"
            reward = 0.02
            
        elif action.command == "CHECK_ROUTES":
            feedback = f"Available routes: GROUND ($50, 5 days), AIR_FREIGHT ($200, 1 day)"
            reward = 0.02
            
        elif action.command == "REROUTE_ORDER":
            reward, feedback = self._handle_reroute(action)
            
        elif action.command == "WAIT":
            feedback = "Agent decided to wait."
            reward = -0.05 # Penalty for doing nothing
            
        else:
            feedback = f"Unknown command: {action.command}"
            reward = -0.1 # Penalty for hallucinating commands

        # Check Win/Loss conditions
        pending_count = sum(1 for o in self.orders.values() if o["status"] == "pending")
        if pending_count == 0:
            self.done = True
            feedback += " All orders processed!"
            
        # Stop early if bankrupt
        if self.budget < 0:
            self.done = True
            feedback += " OVER BUDGET! Bankrupt."

        # Calculate final normalized score (0.0 to 1.0) for the grader
        score = self._calculate_score()
        info = {"score": float(score)}

        return self.state(feedback), reward, self.done, info

    def _handle_reroute(self, action: SupplyAction) -> Tuple[float, str]:
        if not action.order_id or action.order_id not in self.orders:
            return -0.2, f"Invalid or missing order_id: {action.order_id}"
            
        if self.orders[action.order_id]["status"] == "completed":
            return -0.1, f"Order {action.order_id} is already completed."
            
        if action.source_warehouse not in self.inventory:
            return -0.2, f"Invalid warehouse: {action.source_warehouse}"
            
        if action.shipping_method not in SHIPPING_COSTS:
            return -0.2, f"Invalid shipping method: {action.shipping_method}"

        # Constraints Check
        cost = SHIPPING_COSTS[action.shipping_method]
        if self.budget - cost < 0:
            return -0.5, f"Budget exceeded! {action.shipping_method} costs ${cost}, but only ${self.budget} remaining."
            
        if self.inventory[action.source_warehouse] <= 0:
            return -0.5, f"Out of stock at {action.source_warehouse}!"

        # Execute successful route
        self.inventory[action.source_warehouse] -= 1
        self.budget -= cost
        self.orders[action.order_id]["status"] = "completed"
        self.completed += 1
        
        # High reward for successfully routing an order
        return 0.5, f"Success! {action.order_id} routed from {action.source_warehouse} via {action.shipping_method}. Cost: ${cost}."

    def _calculate_score(self) -> float:
        if self.total_orders == 0:
            return 0.1
        
        if self.budget < 0:
            return 0.1
            
        raw_percentage = self.completed / self.total_orders
        
        # Formula: 0.1 se start hoga, aur maximum 0.95 tak jayega
        # Score = 0.1 + (0.85 * raw_percentage)
        score = 0.1 + (raw_percentage * 0.85)
        
        return round(float(score), 2)