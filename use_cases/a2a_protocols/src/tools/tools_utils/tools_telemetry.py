import time
from functools import wraps
from use_cases.a2a_protocols.src.agents import user_proxy

def measure_latency(func):
    """
    Async decorator to measure the execution time of a tool 
    and broadcast the latency metrics directly to the WebSocket frontend.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Record the exact start time
        start_time = time.time()
        
        # Await the execution of the original tool (e.g., getting docker logs)
        result = await func(*args, **kwargs)
        
        # Calculate elapsed time in milliseconds
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        
        # Broadcast the telemetry data silently to the frontend
        if hasattr(user_proxy, "websocket") and user_proxy.websocket:
            try:
                await user_proxy.websocket.send_json({
                    "type": "status",
                    "content": f"[TELEMETRY] Tool '{func.__name__}' executed in {elapsed_ms} ms."
                })
            except Exception:
                # Fail silently so telemetry doesn't crash the main process
                pass
                
        return result
    return wrapper