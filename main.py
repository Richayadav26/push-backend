# # main.py
# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from pywebpush import webpush, WebPushException
# import sqlite3, json
# from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS, DATABASE

# # ✅ Create FastAPI app first
# app = FastAPI(title="PWA Push Notifications Backend")

# # ✅ Setup CORS
# origins = [
#     "http://localhost:3001",  # React PWA dev URL
#     "http://127.0.0.1:3001",
#     "http://localhost:3000",  # optional
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ Setup SQLite DB (change to production DB as needed)
# conn = sqlite3.connect(DATABASE, check_same_thread=False)
# c = conn.cursor()
# c.execute("""
# CREATE TABLE IF NOT EXISTS subscriptions (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     endpoint TEXT UNIQUE,
#     p256dh TEXT,
#     auth TEXT
# )
# """)
# conn.commit()

# # ✅ Subscribe endpoint
# @app.post("/subscribe")
# async def subscribe(request: Request):
#     data = await request.json()
#     endpoint = data.get("endpoint")
#     keys = data.get("keys", {})
#     if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
#         return {"success": False, "error": "Invalid subscription data"}
    
#     # Insert into DB (ignore if already exists)
#     c.execute(
#         "INSERT OR IGNORE INTO subscriptions(endpoint, p256dh, auth) VALUES (?, ?, ?)",
#         (endpoint, keys["p256dh"], keys["auth"])
#     )
#     conn.commit()
#     return {"success": True}

# # ✅ Send notification endpoint
# @app.post("/send_notification")
# async def send_notification(request: Request):
#     data = await request.json()  # Example: {"title": "...", "body": "..."}
    
#     c.execute("SELECT endpoint, p256dh, auth FROM subscriptions")
#     subscriptions = c.fetchall()
    
#     for endpoint, p256dh, auth in subscriptions:
#         sub_info = {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}
#         try:
#             webpush(
#                 subscription_info=sub_info,
#                 data=json.dumps(data),
#                 vapid_private_key=VAPID_PRIVATE_KEY,
#                 vapid_claims=VAPID_CLAIMS
#             )
#         except WebPushException as ex:
#             print(f"Push failed for {endpoint}: {repr(ex)}")
    
#     return {"success": True}


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pywebpush import webpush, WebPushException
from pymongo import MongoClient
import json
from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS, MONGO_URI, DB_NAME
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Push notification server running"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="PWA Push Notifications Backend")

# CORS settings
origins = ["https://icpdelhistage.nvli.in", "http://localhost:3001", "http://127.0.0.1:3001"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# MongoDB Setup
# -----------------------------
#MONGO_URI = "mongodb+srv://pwa_user:fGvsJEsHhyIarPOk@notification-cluster.mk27dbv.mongodb.net/pwa_notifications?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

print("MongoDB connected")
print(db.list_collection_names())


subscriptions_collection = db["subscriptions"]


# -----------------------------
# Subscribe Endpoint
# -----------------------------
# @app.post("/subscribe")
# async def subscribe(request: Request):
#     data = await request.json()
#     endpoint = data.get("endpoint")
#     keys = data.get("keys", {})

#     if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
#         return {"success": False, "error": "Invalid subscription data"}

#     # Store subscriber in MongoDB (upsert)
#     subscriptions_collection.update_one(
#         {"endpoint": endpoint},
#         {"$set": {"keys": keys}},
#         upsert=True
#     )
#     return {"success": True}
# @app.post("/subscribe")
# async def subscribe(request: Request):
#     try:
#         data = await request.json()
#         print("Incoming data:", data)

#         endpoint = data.get("endpoint")
#         keys = data.get("keys", {})

#         if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
#             return {"success": False, "error": "Invalid subscription data"}

#         subscriptions_collection.update_one(
#             {"endpoint": endpoint},
#             {"$set": {"keys": keys}},
#             upsert=True
#         )

#         return {"success": True}

    # except Exception as e:
    #     print("ERROR:", str(e))
    #     return {"success": False, "error": str(e)}
@app.post("/subscribe")
async def subscribe(request: Request):

    data = await request.json()

    print("Subscription received:", data)

    subscriptions_collection.insert_one(data)

    return {"success": True}

# -----------------------------
# Send Notification Endpoint
# -----------------------------
# @app.post("/send_notification")
# async def send_notification(request: Request):
#     data = await request.json()  # Example: {"title": "...", "body": "..."}
    
#     all_subscribers = subscriptions_collection.find({})
    
#     for subscriber in all_subscribers:
#         sub_info = {"endpoint": subscriber["endpoint"], "keys": subscriber["keys"]}
#         try:
#             webpush(
#                 subscription_info=sub_info,
#                 data=json.dumps(data),
#                 vapid_private_key=VAPID_PRIVATE_KEY,
#                 vapid_claims=VAPID_CLAIMS
#             )
#         except WebPushException as ex:
#             print(f"Push failed for {subscriber['endpoint']}: {repr(ex)}")
    
#     return {"success": True}

@app.post("/send_notification")
async def send_notification(request: Request):

    data = await request.json()

    subscribers = list(subscriptions_collection.find())

    for sub in subscribers:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub["endpoint"],
                    "keys": sub["keys"]
                },
                data=json.dumps(data),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
        except Exception as e:
            print("Push error:", e)

    return {"success": True}

# from fastapi import FastAPI, Request
# from pywebpush import webpush, WebPushException
# import sqlite3, json
# from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS, DATABASE
# from fastapi.middleware.cors import CORSMiddleware

# app = FastAPI(title="PWA Push Notifications Backend")
# origins = [
#     "http://localhost:3001",  # React PWA URL
#     "http://127.0.0.1:3001",
#     "http://localhost:3000"   # sometimes needed
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,       # allow your frontend origin
#     allow_credentials=True,
#     allow_methods=["*"],         # allow all HTTP methods
#     allow_headers=["*"],         # allow all headers
# )


# # SQLite DB
# conn = sqlite3.connect(DATABASE, check_same_thread=False)
# c = conn.cursor()
# c.execute("""
# CREATE TABLE IF NOT EXISTS subscriptions (
#     id INTEGER PRIMARY KEY AUTOINCREMENT,
#     endpoint TEXT UNIQUE,
#     p256dh TEXT,
#     auth TEXT
# )
# """)
# conn.commit()

# @app.post("/subscribe")
# async def subscribe(request: Request):
#     data = await request.json()
#     endpoint = data["endpoint"]
#     keys = data["keys"]
#     c.execute("INSERT OR IGNORE INTO subscriptions(endpoint, p256dh, auth) VALUES (?, ?, ?)",
#               (endpoint, keys["p256dh"], keys["auth"]))
#     conn.commit()
#     return {"success": True}

# @app.post("/send_notification")
# async def send_notification(request: Request):
#     data = await request.json()
#     c.execute("SELECT endpoint, p256dh, auth FROM subscriptions")
#     subscriptions = c.fetchall()
    
#     for endpoint, p256dh, auth in subscriptions:
#         sub_info = {"endpoint": endpoint, "keys": {"p256dh": p256dh, "auth": auth}}
#         try:
#             webpush(subscription_info=sub_info,
#                     data=json.dumps(data),
#                     vapid_private_key=VAPID_PRIVATE_KEY,
#                     vapid_claims=VAPID_CLAIMS)
#         except WebPushException as ex:
#             print("Push failed:", repr(ex))
#     return {"success": True}