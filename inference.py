import asyncio
import json
import os
import textwrap
from typing import List, Optional

from openai import OpenAI
from pydantic import ValidationError

from open_supply.env import OpenSupplyEnv
from open_supply.models import SupplyAction

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"

# We will test against the Hard task for the baseline
TASK_NAME = os.getenv("MY_ENV_V4_TASK", "hard_optimization")
BENCHMARK = os.getenv("MY_ENV_V4_BENCHMARK", "open_supply")
MAX_STEPS = 30
TEMPERATURE = 0.2 # Low temperature for more deterministic JSON outputs
SUCCESS_SCORE_THRESHOLD = 0.1

SYSTEM_PROMPT = textwrap.dedent(
    """
    You are an autonomous AI Logistics Manager.
    Your goal is to route all pending orders successfully before budget runs out.
    
    AVAILABLE OPTIONS:
    - Warehouses: "Warehouse_CHI" , "Warehouse_LA"
    - Shipping Methods: "GROUND" ($50), "AIR_FREIGHT" ($200)

    WORKFLOW:
    1. If you don't know the orders, use "CHECK_ORDERS".
    2. Once you know a pending order_id, immediately use "REROUTE_ORDER".
    
    You must output your action as a valid JSON object matching this schema:
    {
      "command": "CHECK_INVENTORY" | "CHECK_ROUTES" | "CHECK_ORDERS" | "REROUTE_ORDER" | "WAIT",
      "order_id": "ORD-XXX" (optional, required for REROUTE_ORDER),
      "source_warehouse": "Warehouse_CHI" or "Warehouse_LA" (optional, required for REROUTE_ORDER),
      "shipping_method": "GROUND" or "AIR_FREIGHT" (optional, required for REROUTE_ORDER)
    }
    Reply ONLY with valid JSON. No markdown formatting, no explanations.
    """
).strip()

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error.replace('\n', ' ') if error else "null"
    done_val = str(done).lower()
    # Action string cannot have newlines in the required stdout format
    clean_action = action.replace('\n', ' ')
    print(
        f"[STEP] step={step} action={clean_action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def build_user_prompt(step: int, observation: dict, last_feedback: str, history: List[str]) -> str:
    return textwrap.dedent(
        f"""
        Step: {step}
        Current State: {json.dumps(observation, default=str)}
        Feedback from last action: {last_feedback}
        
        Analyze the state and provide your next JSON action.
        """
    ).strip()

def get_model_action(client: OpenAI, step: int, observation: dict, last_feedback: str, history: List[str]) -> str:
    user_prompt = build_user_prompt(step, observation, last_feedback, history)
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[DEBUG] Model request failed: {exc}", flush=True)
        return '{"command": "WAIT"}'

def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    # Initialize the Environment locally for the baseline script
    env = OpenSupplyEnv(task_name=TASK_NAME)
    
    history: List[str] = []
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=TASK_NAME, env=BENCHMARK, model=MODEL_NAME)

    try:
        obs = env.reset()
        last_feedback = obs.last_action_feedback

        for step in range(1, MAX_STEPS + 1):
            raw_action_str = get_model_action(client, step, obs.model_dump(), last_feedback, history)
            
            error = None
            reward = 0.0
            done = False
            
            # 1. Parse LLM Output to Pydantic
            try:
                # Clean markdown blocks if the LLM hallucinated them
                clean_json_str = raw_action_str.replace('```json', '').replace('```', '').strip()
                action_dict = json.loads(clean_json_str)
                action_obj = SupplyAction(**action_dict)
                
                # 2. Step the Environment
                obs, reward, done, info = env.step(action_obj)
                last_feedback = obs.last_action_feedback
                
            except (json.JSONDecodeError, ValidationError) as e:
                # Penalize the LLM heavily for breaking the JSON contract
                error = f"Invalid format: {str(e)}"
                reward = -0.5 
                last_feedback = error
                # We do not step the env, but we consume a step in the loop
            
            rewards.append(reward)
            steps_taken = step
            
            log_step(step=step, action=raw_action_str, reward=reward, done=done, error=error)
            history.append(f"Step {step}: {raw_action_str} -> reward {reward:+.2f}")

            if done:
                score = info.get("score", 0.0)
                break

        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    main()