import discord
import dotenv
import os
from motor import motor_tornado

dotenv.load_dotenv()

client: motor_tornado.MotorClient = motor_tornado.MotorClient(os.getenv("MONGO_URI"))
database: motor_tornado.MotorDatabase = client["sally"]

async def add_date(date_id: str, date: str, tickets_amount: str, role: int):

    collection: motor_tornado.MotorCollection = database["dates"]
    data = {"date_id": date_id, "date": date, "role": role, "tickets_amount": tickets_amount, "tickets_sold": 0, "tickets_available": tickets_amount}

    return await collection.insert_one(data)

async def edit_date(date_id: str, new_data: dict):

    collection = database["dates"]
    return collection.find_one_and_update({"date_id": date_id}, {"$set": new_data})

async def get_date(date_id: str):
    collection: motor_tornado.MotorCollection = database["dates"]
    return await collection.find_one({"date_id": date_id})

async def return_dates():
    
    collection = database["dates"]
    find = collection.find()
    dates = []
    for date in await find.to_list(length=None):
        dates.append(date)

    return dates

async def add_queue(id: int, channel: int):
    collection: motor_tornado.MotorCollection = database["queues"]
    data = {"name": "queue", "message": id, "channel": channel}

    return await collection.insert_one(data)

async def get_queue_message():
    collection: motor_tornado.MotorCollection = database["queues"]
    data = {"name": "queue"}

    queue = await collection.find_one(data)
    return queue["message"], queue["channel"]