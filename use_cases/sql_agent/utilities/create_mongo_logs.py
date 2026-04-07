from pymongo import MongoClient
from datetime import datetime, timedelta
import random

def seed_mongo():
    client = MongoClient("mongodb://host.docker.internal:27017/")
    
    db = client["company_logs"]
    collection = db["server_logs"]

    collection.drop()

    endpoints = ["/home", "/api/v1/users", "/api/v1/checkout", "/login", "/ask-sql"]
    methods = ["GET", "POST", "PUT", "DELETE"]
    
    logs = []
    base_time = datetime.now()

    for i in range(100):
        is_error = random.random() < 0.2
        level = random.choice(["ERROR", "CRITICAL"]) if is_error else "INFO"
        status_code = random.choice([400, 401, 500, 502]) if is_error else 200
        
        log_document = {
            "timestamp": base_time - timedelta(minutes=random.randint(1, 10000)),
            "level": level,
            "endpoint": random.choice(endpoints),
            "method": random.choice(methods),
            "status_code": status_code,
            "response_time_ms": random.randint(10, 2000),
            "metadata": {
                "user_agent": "Mozilla/5.0" if random.random() > 0.5 else "curl/7.68.0",
                "ip_address": f"192.168.1.{random.randint(1, 255)}"
            }
        }
        
        if is_error:
            log_document["error_message"] = "Connection timed out" if status_code >= 500 else "Unauthorized access"
            
        logs.append(log_document)

    collection.insert_many(logs)
    print(f"Success! Inserted {len(logs)} logs into MongoDB 'company_logs.server_logs'")

if __name__ == "__main__":
    seed_mongo()