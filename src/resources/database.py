import discord
import dotenv
import os
from motor import motor_tornado

dotenv.load_dotenv()

client: motor_tornado.MotorClient = motor_tornado.MotorClient(
  os.getenv("MONGO_URI"))
database: motor_tornado.MotorDatabase = client["sally"]


async def find_one(col: str, data: dict):
  collection = database[col]
  return await collection.find_one(data)


async def insert_one(col: str, data: dict):
  collection = database[col]
  return await collection.insert_one(data)


async def update_one(col: str, check: dict, data: dict):
  collection = database[col]
  return await collection.find_one_and_update(check, {"$set": data})


async def delete_one(col: str, data: dict):
  collection = database[col]
  return await collection.delete_one(data)


async def return_all(col: str, filter: dict = {}):
  collection = database[col]
  find = collection.find(filter)
  docs = []
  for doc in await find.to_list(None):
    docs.append(doc)

  return docs


async def add_date(guild_id: int, date_id: str, date: str, tickets_amount: str,
                   role: int):

  collection: motor_tornado.MotorCollection = database["dates"]
  data = {
    "guild_id": guild_id,
    "date_id": date_id,
    "date": date,
    "role": role,
    "tickets_amount": tickets_amount,
    "tickets_sold": 0,
    "tickets_available": tickets_amount
  }

  return await collection.insert_one(data)


async def edit_date(date_id: str, new_data: dict):

  collection = database["dates"]
  return collection.find_one_and_update({"date_id": date_id},
                                        {"$set": new_data})


async def get_date(date_id: str):
  collection: motor_tornado.MotorCollection = database["dates"]
  return await collection.find_one({"date_id": date_id})


async def return_dates(guild_id: int):

  collection = database["dates"]
  find = collection.find({"guild_id": guild_id})
  dates = []
  for date in await find.to_list(None):
    dates.append(date)

  return dates


async def delete_date(date_id: str):
  collection = database["dates"]
  return await collection.delete_one({"date_id": date_id})


async def add_queue(queue_id: int, id: int, channel: int):
  collection: motor_tornado.MotorCollection = database["queues"]
  data = {"queue_id": queue_id, "message": id, "channel": channel}

  return await collection.insert_one(data)


async def get_queue_message(queue_id: int):
  collection: motor_tornado.MotorCollection = database["queues"]
  data = {"queue_id": queue_id}

  queue = await collection.find_one(data)
  if queue:
    return queue["message"], queue["channel"]
  return None
