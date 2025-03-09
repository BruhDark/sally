import discord
import dotenv
import os
from motor import motor_tornado
from pymongo import ReturnDocument
from pymongo import results

dotenv.load_dotenv()

client: motor_tornado.MotorClient = motor_tornado.MotorClient(
    os.getenv("MONGO_URI"))  # type: ignore
database: motor_tornado.MotorDatabase = client["sally"]  # type: ignore

# GENERIC FUNCTIONS


async def find(col: str, data: dict):
    collection = database[col]
    return await collection.find(data).to_list(None)


async def find_one(col: str, data: dict):
    collection = database[col]
    return await collection.find_one(data)


async def insert_one(col: str, data: dict):
    collection = database[col]
    return await collection.insert_one(data)


async def update_one(col: str, check: dict, data: dict):
    collection = database[col]
    return await collection.find_one_and_update(check, {"$set": data}, return_document=ReturnDocument.AFTER)


async def delete_one(col: str, data: dict) -> results.DeleteResult:
    collection = database[col]
    return await collection.delete_one(data)


async def return_all(col: str, filter: dict = {}):
    collection = database[col]
    find = await collection.find(filter)
    return find.to_list(None)


# VERIFICATION

async def add_roblox_info(user_id: str, roblox_id: str, data: dict):
    collection = database["roblox_verifications"]
    data = {"user_id": str(user_id), "roblox_id": str(
        roblox_id), "data": data, "blacklisted": False}
    return await collection.insert_one(data)


async def update_roblox_info(user_id: str, roblox_id: str, data: dict):
    collection = database["roblox_verifications"]
    check = {"user_id": str(user_id)}
    new_data = {"roblox_id": str(roblox_id), "data": data}
    return await collection.find_one_and_update(check, {"$set": new_data}, return_document=ReturnDocument.AFTER)


async def get_roblox_info(user_id: str):
    collection = database["roblox_verifications"]
    return await collection.find_one({"user_id": str(user_id)})


async def get_roblox_info_by_rbxid(roblox_id: str):
    collection = database["roblox_verifications"]
    return await collection.find_one({"roblox_id": str(roblox_id)})


async def delete_roblox_info(user_id: str) -> results.DeleteResult:
    collection = database["roblox_verifications"]
    return await collection.delete_one({"user_id": str(user_id)})


async def blacklist_roblox_user(user_id: str, reason: str):
    collection = database["roblox_verifications"]
    check = {"user_id": str(user_id)}
    new_data = {"blacklisted": True, "message": reason}
    return await collection.find_one_and_update(check, {"$set": new_data}, return_document=ReturnDocument.AFTER)


async def remove_blacklist_roblox(user_id: str):
    collection = database["roblox_verifications"]
    check = {"user_id": str(user_id)}
    new_data = {"blacklisted": False}
    return await collection.find_one_and_update(check, {"$set": new_data}, return_document=ReturnDocument.AFTER)

# EVENTS


async def add_show(message_id: int, event_id: int):
    collection = database["shows"]
    data = {"_id": message_id, "event_id": event_id}

    return await collection.insert_one(data)


async def get_show(message_id: int):
    collection = database["shows"]
    return await collection.find_one({"_id": message_id})


async def delete_show(message_id: int):
    collection = database["shows"]
    return await collection.delete_one({"_id": message_id})

# POLL FUNCTIONS


async def create_poll(poll_id: int, choices: list):
    collection = database["polls"]
    data = {"_id": poll_id, "status": "INACTIVE",
            "total_votes": 0, "choices": choices, "users": []}

    for choice in choices:
        data[choice] = 0

    return await collection.insert_one(data)


async def get_poll(poll_id: int):
    collection = database["polls"]
    return await collection.find_one({"_id": poll_id})


async def add_vote(poll_id: int, voter_id: int, choice: str):
    collection = database["polls"]
    new_data = {"$addToSet": {f"users": voter_id},
                "$inc": {"total_votes": 1, choice: 1}}

    return await collection.find_one_and_update({"_id": poll_id}, new_data, return_document=ReturnDocument.AFTER)


async def remove_vote(poll_id: int, voter_id: int, choice: str):
    collection = database["polls"]
    new_data = {"$pull": {f"users": voter_id},
                "$inc": {"total_votes": -1, choice: -1}}

    return await collection.find_one_and_update({"_id": poll_id}, new_data, return_document=ReturnDocument.AFTER)


async def change_poll_status(poll_id: int, status: str | None):
    collection = database["polls"]
    return await collection.find_one_and_update({"_id": poll_id}, {"$set": {"PID": status}}, return_document=ReturnDocument.AFTER)


async def get_active_poll():
    collection = database["polls"]
    return await collection.find_one({"status": "ACTIVE"})


async def delete_poll(message_id: int):
    collection = database["polls"]

    return await collection.delete_one({"_id": message_id})

# DATES FUNCTIONS


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
