from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pywebpush import webpush, WebPushException
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
import json
import datetime
import uvicorn
import uuid

from config import (
    VAPID_PRIVATE_KEY,
    VAPID_CLAIMS,
    MONGO_URI,
    DB_NAME
)

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="PWA Push Notifications Backend")

# -----------------------------
# CORS
# -----------------------------
origins = [
    "https://icpdelhistage.nvli.in",
    "https://indianculture.gov.in",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# MongoDB
# -----------------------------
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

subscriptions_collection = db["subscriptions"]
notifications_collection = db["notifications"]
scheduled_collection = db["scheduled_notifications"]

print("MongoDB Connected")

# -----------------------------
# Scheduler
# -----------------------------
scheduler = BackgroundScheduler()
scheduler.start()


# -----------------------------
# Helper: Send Push
# -----------------------------
def push_to_subscribers(payload, page=None):

    if page:
        subscribers = subscriptions_collection.find({"page": page})
    else:
        subscribers = subscriptions_collection.find({"endpoint": {"$exists": True}})

    success = 0
    failed = 0

    for subscriber in subscribers:

        try:
            webpush(
                subscription_info={
                    "endpoint": subscriber["endpoint"],
                    "keys": subscriber["keys"]
                },
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )

            success += 1

        except WebPushException as ex:

            print("Push failed:", ex)

            # remove expired subscriptions
            if "410" in str(ex) or "404" in str(ex):
                subscriptions_collection.delete_one(
                    {"endpoint": subscriber["endpoint"]}
                )

            failed += 1

    return success, failed


# -----------------------------
# Scheduled Notification Check
# -----------------------------
def check_scheduled():

    now = datetime.datetime.utcnow()

    items = scheduled_collection.find({
        "schedule": {"$lte": now}
    })

    for item in items:

        payload = {
            "id": str(uuid.uuid4()),
            "title": item.get("title"),
            "body": item.get("body"),
            "image": item.get("image"),
            "url": item.get("url"),
            "icon": "/notification-icon.png",
            "badge": "/badge-icon.png",
            "time": str(datetime.datetime.utcnow()),
            "clicks": 0
        }

        push_to_subscribers(payload)

        notifications_collection.insert_one(payload)

        scheduled_collection.delete_one({"_id": item["_id"]})


scheduler.add_job(check_scheduled, "interval", minutes=1)

# -----------------------------
# Health Check
# -----------------------------
@app.get("/")
def home():
    return {"status": "Push notification server running"}

# -----------------------------
# Subscribe
# -----------------------------
@app.post("/subscribe")
async def subscribe(request: Request):

    data = await request.json()
    endpoint = data.get("endpoint")

    if not endpoint:
        return {"success": False, "message": "Invalid subscription"}

    page = data.get("page", "/")

    subscriptions_collection.update_one(
        {"endpoint": endpoint},
        {
            "$set": {
                "endpoint": endpoint,
                "keys": data["keys"],
                "page": page
            }
        },
        upsert=True
    )

    return {"success": True}


# -----------------------------
# Subscriber Count
# -----------------------------
@app.get("/subscriber_count")
async def subscriber_count():

    count = subscriptions_collection.count_documents(
        {"endpoint": {"$exists": True}}
    )

    return {"count": count}


# -----------------------------
# Send Notification
# -----------------------------
@app.post("/send_notification")
async def send_notification(request: Request):

    data = await request.json()

    payload = {
        "id": str(uuid.uuid4()),
        "title": data.get("title"),
        "body": data.get("body"),
        "image": data.get("image"),
        "url": data.get("url"),
        "icon": "/notification-icon.png",
        "badge": "/badge-icon.png",
        "time": str(datetime.datetime.utcnow()),
        "clicks": 0
    }

    page = data.get("page")

    success, failed = push_to_subscribers(payload, page)

    notifications_collection.insert_one(payload)

    return {
        "success": True,
        "sent": success,
        "failed": failed
    }


# -----------------------------
# Schedule Notification
# -----------------------------
@app.post("/schedule_notification")
async def schedule_notification(request: Request):

    data = await request.json()

    data["schedule"] = datetime.datetime.fromisoformat(data["schedule"])

    scheduled_collection.insert_one(data)

    return {"success": True}


# -----------------------------
# Notification History
# -----------------------------
@app.get("/notifications")
async def notifications():

    items = list(
        notifications_collection
        .find()
        .sort("_id", -1)
        .limit(20)
    )

    for item in items:
        item["_id"] = str(item["_id"])

    return items


# -----------------------------
# Track Notification Click
# -----------------------------
@app.post("/track_click")
async def track_click(request: Request):

    data = await request.json()

    notifications_collection.update_one(
        {"id": data.get("id")},
        {"$inc": {"clicks": 1}}
    )

    return {"success": True}


# -----------------------------
# Analytics
# -----------------------------
@app.get("/analytics")
async def analytics():

    total_notifications = notifications_collection.count_documents({})

    total_clicks_cursor = notifications_collection.aggregate([
        {"$group": {"_id": None, "clicks": {"$sum": "$clicks"}}}
    ])

    clicks = 0
    for item in total_clicks_cursor:
        clicks = item["clicks"]

    return {
        "notifications_sent": total_notifications,
        "total_clicks": clicks
    }


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)