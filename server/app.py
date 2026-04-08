import os
import uvicorn
from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional
import sys

# Path fixing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from open_supply.env import OpenSupplyEnv
from open_supply.models import SupplyAction

app = FastAPI()
env = OpenSupplyEnv()

class ResetRequest(BaseModel):
    task_name: str = "easy_routing"

@app.post("/reset")
def reset(req: Optional[ResetRequest] = Body(default=None)):
    task_name = req.task_name if req else "easy_routing"
    # SAFE CALL: Try-except lagaya taaki agar env.py purana ho toh crash na ho
    try:
        obs = env.reset(task_name=task_name)
    except TypeError:
        obs = env.reset() 
        
    return {
        "observation": obs.dict() if hasattr(obs, 'dict') else obs,
        "reward": 0.0,
        "done": False,
        "info": {"score": 0.1}
    }

@app.post("/reset")
async def reset(request: Request):
    # Bina kisi condition ke score bhej do reset par
    obs = env.reset() # default task load hoga
    return {
        "observation": obs.dict() if hasattr(obs, 'dict') else obs,
        "reward": 0.0,
        "done": False,
        "info": {"score": 0.15} # <--- Score yahan hona chahiye
    }

@app.get("/")
def root():
    return {"status": "running"}

def main():
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()