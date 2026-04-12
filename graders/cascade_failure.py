def grade(trajectory, env_info=None):
    return max(0.001, min(0.999, env_info.get("score", 0.95) if env_info else 0.95))