# Open-Supply: AI Logistics Optimization Environment

Open-Supply is a real-world supply chain and logistics routing environment built on the OpenEnv spec. It challenges AI agents to act as Logistics Managers, routing pending orders across multiple warehouses while strictly adhering to budget and inventory constraints.

## 🎯 The Tasks
The environment features 3 distinct tasks of increasing difficulty to evaluate agent decision-making and planning:
1. **easy_routing:** A basic baseline task. The agent must route a single pending order. Budget and inventory are practically unlimited. Tests fundamental tool usage.
2. **medium_budget:** The agent must route 3 orders but faces a tight budget constraint ($150). It must selectively choose cost-effective shipping methods (GROUND) over expensive ones (AIR_FREIGHT) to avoid bankruptcy.
3. **hard_optimization:** The agent must route 5 orders with strict budget limits and asymmetric inventory (Chicago warehouse is critically low). The agent must query inventory states and load-balance routing between warehouses.

## 📊 Environment Spaces

### Action Space (JSON)
The agent must output a structured JSON action matching this schema:
- `command` (str): One of `CHECK_INVENTORY`, `CHECK_ROUTES`, `CHECK_ORDERS`, `REROUTE_ORDER`, `WAIT`.
- `order_id` (str, optional): The target order to route (e.g., "ORD-001").
- `source_warehouse` (str, optional): "Warehouse_CHI" or "Warehouse_LA".
- `shipping_method` (str, optional): "GROUND" or "AIR_FREIGHT".

### Observation Space
The environment returns a structured state:
- `budget_remaining` (float): Current available funds.
- `pending_orders` (int): Number of orders yet to be fulfilled.
- `completed_orders` (int): Number of successfully routed orders.
- `last_action_feedback` (str): Textual feedback (success, errors, or requested data).
- `is_done` (bool): Episode termination flag.

## 🏆 Reward & Grading Function
The environment provides dense, partial rewards to guide the agent:
- **Information Gathering:** +0.02 (for checking inventory, orders, etc.)
- **Successful Reroute:** +0.50 per order.
- **Penalties:** -0.05 for waiting/stalling, -0.1 to -0.5 for hallucinated commands or violating constraints (budget/inventory).
- **Final Grader Score:** The final score is deterministic [0.0, 1.0], calculated as `completed_orders / total_orders`, evaluated only if the agent stays within budget.

## 🚀 Setup & Testing

**1. Run the Docker Backend:**
```bash
docker build -t open-supply .
docker run -p 7860:7860 open-supply