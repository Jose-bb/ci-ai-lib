def calculate_turn_cost(prompt_tokens: int, completion_tokens: int, model_name: str = "gpt-4o-mini") -> float:
    """
    Calculates the financial cost of a single LLM turn based on token usage.
    Returns the total cost in USD rounded to 5 decimal places to support lightweight models.
    """
    # Standard pricing per 1,000 tokens (in USD)
    pricing_tiers = {
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4-turbo": {"prompt": 0.010, "completion": 0.030},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.00060},
    }
    
    # Fallback to gpt-4o-mini pricing if the model is not found
    rates = pricing_tiers.get(model_name.lower(), pricing_tiers["gpt-4o-mini"])
    
    prompt_cost = (prompt_tokens / 1000.0) * rates["prompt"]
    completion_cost = (completion_tokens / 1000.0) * rates["completion"]
    
    total_cost = prompt_cost + completion_cost
    
    return round(total_cost, 5)

def format_telemetry_cost(agent_name: str, total_tokens: int, cost_usd: float) -> str:
    """Formats the cost data into a clean telemetry string for the Frontend."""
    return f"[TELEMETRY] {agent_name} usage: {total_tokens} tokens | Cost: ${cost_usd:.5f}"