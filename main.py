from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pywebpush import webpush, WebPushException
from pymongo import MongoClient
import json
import datetime
import uvicorn

from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS, MONGO_URI, DB_NAME

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(title="PWA Push Notifications Backend")

@app.get("/")
def home():
    return {"status": "Push notification server running"}

# -----------------------------
# CORS
# -----------------------------
origins = [
    "https://icpdelhistage.nvli.in",
    "http://localhost:3001",
    "http://localhost:3000",
    "https://indianculture.gov.in",
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

print("MongoDB connected")
print(db.list_collection_names())

subscriptions_collection = db["subscriptions"]
notifications_collection = db["notifications"]

# -----------------------------
# Subscribe
# -----------------------------
@app.post("/subscribe")
async def subscribe(request: Request):

    data = await request.json()

    endpoint = data.get("endpoint")

    if not endpoint:
        return {"success": False, "message": "Invalid subscription"}

    existing = subscriptions_collection.find_one({"endpoint": endpoint})

    if existing:
        return {"success": True, "message": "Already subscribed"}

    subscriptions_collection.insert_one(data)

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
# @app.post("/send_notification")
# async def send_notification(request: Request):

#     data = await request.json()

#     title = data.get("title")
#     body = data.get("body")
#     image = data.get("image")
#     url = data.get("url")

#     payload = {
#         "title": title,
#         "body": body,
#         "image": image,
#         "url": url,
#         "time": str(datetime.datetime.now())
#     }

#     subscribers = subscriptions_collection.find(
#         {"endpoint": {"$exists": True}}
#     )

#     for subscriber in subscribers:
#         try:

#             webpush(
#                 subscription_info={
#                     "endpoint": subscriber["endpoint"],
#                     "keys": subscriber["keys"]
#                 },
#                 data=json.dumps(payload),
#                 vapid_private_key=VAPID_PRIVATE_KEY,
#                 vapid_claims=VAPID_CLAIMS
#             )

#         except WebPushException as ex:
#             print("Push failed:", ex)

#     notifications_collection.insert_one(payload)

#     return {"success": True}

@app.post("/send_notification")
async def send_notification(request: Request):

    data = await request.json()

    title = data.get("title")
    body = data.get("body")
    image = data.get("image")
    url = data.get("url")

    payload = {
        "title": title,
        "body": body,
        "image": image,
        "url": url,
        "time": str(datetime.datetime.utcnow())
    }

    subscribers = subscriptions_collection.find(
        {"endpoint": {"$exists": True}}
    )

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

        except WebPushException as ex:
            print("Push failed:", ex)

    notifications_collection.insert_one(payload)

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

    for i in items:
        i["_id"] = str(i["_id"])

    return items



# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)

    

# from fastapi import FastAPI, Request
# from fastapi.middleware.cors import CORSMiddleware
# from pywebpush import webpush, WebPushException
# from pymongo import MongoClient
# import json
# from config import VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY, VAPID_CLAIMS, MONGO_URI, DB_NAME
# import uvicorn
# from fastapi import FastAPI

# app = FastAPI()

# @app.get("/")
# def home():
#     return {"status": "Push notification server running"}

# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=10000)
# # -----------------------------
# # FastAPI App
# # -----------------------------
# app = FastAPI(title="PWA Push Notifications Backend")

# # CORS settings
# origins = ["https://icpdelhistage.nvli.in", "http://localhost:3001", "http://127.0.0.1:3001"]
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # -----------------------------
# # MongoDB Setup
# # -----------------------------
# #MONGO_URI = "mongodb+srv://pwa_user:fGvsJEsHhyIarPOk@notification-cluster.mk27dbv.mongodb.net/pwa_notifications?retryWrites=true&w=majority"
# client = MongoClient(MONGO_URI)
# db = client[DB_NAME]

# print("MongoDB connected")
# print(db.list_collection_names())

# subscriptions_collection = db["subscriptions"]

# notifications_collection = db["notifications"]




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


@app.get("/subscriber_count")
async def subscriber_count():
    count = subscriptions_collection.count_documents({"endpoint": {"$exists": True}})
    return {"count": count}
# @app.get("/subscriber_count")
# async def subscriber_count():
#     count = subscriptions_collection.count_documents({"endpoint": {"$exists": True}})
#     return {"count": count}

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

# @app.post("/send_notification")
# async def send_notification(request: Request):

#     data = await request.json()

#     subscribers = list(subscriptions_collection.find())

#     for sub in subscribers:
#         try:
#             webpush(
#                 subscription_info={
#                     "endpoint": sub["endpoint"],
#                     "keys": sub["keys"]
#                 },
#                 data=json.dumps(data),
#                 vapid_private_key=VAPID_PRIVATE_KEY,
#                 vapid_claims=VAPID_CLAIMS
#             )
#         except Exception as e:
#             print("Push error:", e)

#     return {"success": True}


# @app.post("/send_notification")
# async def send_notification(request: Request):
#     data = await request.json()

#     subscribers = subscriptions_collection.find({"endpoint": {"$exists": True}})

#     for subscriber in subscribers:
#         try:
#             webpush(
#                 subscription_info={
#                     "endpoint": subscriber["endpoint"],
#                     "keys": subscriber["keys"]
#                 },
#                 data=json.dumps(data),
#                 vapid_private_key=VAPID_PRIVATE_KEY,
#                 vapid_claims=VAPID_CLAIMS
#             )

#         except WebPushException as ex:
#             print("Push failed:", ex)

#     return {"success": True}

# @app.post("/send_notification")
# async def send_notification(request: Request):

#     data = await request.json()

#     title = data.get("title")
#     body = data.get("body")
#     image = data.get("image")
#     url = data.get("url")

#     payload = {
#         "title": title,
#         "body": body,
#         "image": image,
#         "url": url
#     }

#     subscribers = subscriptions_collection.find({"endpoint": {"$exists": True}})

#     for subscriber in subscribers:
#         try:
#             webpush(
#                 subscription_info={
#                     "endpoint": subscriber["endpoint"],
#                     "keys": subscriber["keys"]
#                 },
#                 data=json.dumps(payload),
#                 vapid_private_key=VAPID_PRIVATE_KEY,
#                 vapid_claims=VAPID_CLAIMS
#             )

#         except WebPushException as ex:
#             print("Push failed:", ex)

#     return {"success": True}


@app.post("/send_notification")
async def send_notification(request: Request):

    data = await request.json()

    payload = {
        "title": data.get("title"),
        "body": data.get("body"),
        "image": data.get("image"),
        "url": data.get("url"),
        "time": str(datetime.datetime.now())
    }

    subscribers = subscriptions_collection.find({"endpoint": {"$exists": True}})

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

        except WebPushException as ex:
            print("Push failed:", ex)

    # notifications_collection.insert_one(payload)

    notifications_collection.insert_one({
    "title": title,
    "body": body,
    "image": image,
    "url": url
})

    return {"success": True}



@app.get("/notifications")
async def notifications():
    data = list(notifications_collection.find(().sort("_id",-1).limit(20)))

    for i in data:
        i["_id"] = str(i["_id"])

    return data

# @app.get("/notifications")
# async def notifications():
#     items = list(notifications_collection.find().sort("_id",-1).limit(20))
    
#     for i in items:
#         i["_id"] = str(i["_id"])

#     return items
