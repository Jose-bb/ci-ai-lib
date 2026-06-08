from use_cases.a2a_protocols.src.agents import user_proxy

async def request_human_approval(prompt_message: str, success_message: str) -> bool:
    """
    Centralized Human-In-The-Loop (HITL) authorization flow via WebSockets.
    Returns True if approved, False if denied.
    """
    prompt = f"SECURITY ALERT: {prompt_message}\nDo you approve this execution? (y/n): "
    
    while True:
        user_input = await user_proxy.a_get_human_input(prompt)
        user_input = user_input.strip().lower()
        
        if user_input in ['y', 'yes']:
            if hasattr(user_proxy, "websocket") and user_proxy.websocket:
                await user_proxy.websocket.send_json({"type": "status", "content": f"[+] Access GRANTED. {success_message}"})
            return True
            
        elif user_input in ['n', 'no']:
            if hasattr(user_proxy, "websocket") and user_proxy.websocket:
                await user_proxy.websocket.send_json({"type": "status", "content": "[-] Access DENIED by User."})
            return False
            
        else:
            if hasattr(user_proxy, "websocket") and user_proxy.websocket:
                await user_proxy.websocket.send_json({"type": "error", "content": "Invalid input. Please type 'y' for Yes, or 'n' for No."})