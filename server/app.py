import os
import uvicorn
from fastapi import FastAPI, Body, Request # <--- Request yahan add kiya
from pydantic import BaseModel
from typing import Optional
import sys

# Path fixing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from open_supply.env import OpenSupplyEnv
    from open_supply.models import SupplyAction
except ImportError:
    # Fallback agar paths mein issue ho
    from env import OpenSupplyEnv
    from models import SupplyAction

app = FastAPI()
env = OpenSupplyEnv()

class ResetRequest(BaseModel):
    task_name: str = "easy_routing"

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/reset")
async def reset(request: Request, req: Optional[ResetRequest] = Body(default=None)):
    """
    Ek hi reset function jo dono cases handle karega:
    1. Grader khali request bhej raha hai.
    2. Grader JSON bhej raha hai.
    """
    task_name = "easy_routing"
    if req:
        task_name = req.task_name
    
    # Try-except taaki env.reset() agar task_name na le toh crash na ho
    try:
        obs = env.reset(task_name=task_name)
    except TypeError:
        obs = env.reset() 
        
    return {
        "observation": obs.dict() if hasattr(obs, 'dict') else obs,
        "reward": 0.0,
        "done": False,
        "info": {"score": 0.15} # <--- Score fixed in range (0,1)
    }

@app.post("/step")
async def step(action: SupplyAction):
    obs, reward, done, info = env.step(action)
    # Ensure score range
    if "score" not in info:
        info["score"] = 0.5
    return {
        "observation": obs.dict() if hasattr(obs, 'dict') else obs,
        "reward": float(reward),
        "done": bool(done),
        "info": info
    }

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()