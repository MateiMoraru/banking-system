import hashlib
import pymongo
from typing import List
from bson import json_util
import datetime

class Mongo:
    def __init__(self, addr:str="mongodb://localhost:27017/"):
        try:
            self.client = pymongo.MongoClient(addr)
            self.client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError as err:
            print(err)

        self.users = self.client["Banking-system"]["clients"]


    def add_user(self, name:str, pin:str):
        data = {
            "name": name, 
            "pin": pin, 
            "balance": 0,
            "savings": 0,
            "debt": 0,
            "credit": 0,
            "transactions": [],
            "friends": [],
            "friend-requests": [],
            "requests": []
            }
        self.users.insert_one(data)


    def add_credit(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc": {"credit": value}})


    def add_friend(self, name:str, target:str):
        reqs_1 = self.get_friend_requests(name)
        friends_1 = self.get_friends(name)
        reqs_2 = self.get_friend_requests(target)
        friends_2 = self.get_friends(target)
        if (name not in reqs_2 and name not in friends_2) and (target not in reqs_1 and target not in friends_1):
            self.users.find_one_and_update({"name": target}, {"$push": {"friend_requests": name}})
            return f"Friend request sent to {target}!-w"
        if name in reqs_2 or target in reqs_1:
            print("adding friend")
            self.users.find_one_and_update({"name": name}, {"$push": {"friends": target}})
            self.users.find_one_and_update({"name": target}, {"$push": {"friends": name}})
            self.users.find_one_and_update({"name": target}, {"$pull": {"friend_requests": name}})
            if target in reqs_1:
                 self.users.find_one_and_update({"name": name}, {"$pull": {"friend_requests": target}})
            return f"-GREEN-{target} is now your friend!-RESET--w"
        return f"You already have {target} on your friend request list!-w"
    

    def remove_friend(self, name:str, target:str):
        if self.search_name(target):
            if target in self.get_friends(name):
                self.users.find_one_and_update({"name": name}, {"$pull": {"friends": target}})
                return f"Removed {target} from your friend list-w"
            return f"{target} is not in your friend list!-w"
        return f"{target} doesn't exist!-w"
    

    def request(self, name:str, target:str, value:int):
        id = self.transaction_id(date(), name, target, value)
        request = {
            "from": name,
            "to": target,
            "value": value,
            "date": date(),
            "hash": id
        }
        self.users.find_one_and_update({"name": name}, {"$push": {"requests": request}})

    
    def get(self, name:str, field:str):
        try:
            find = self.users.find_one({"name": name})
        except:
            print(f"Unable to find a user called {name}")
        
        if find != None:
            print(find[field])
            return find[field]
        print(None)
        return None


    def get_user_raw(self, name:str):
        find = self.users.find_one({"name": name})
        return find

    
    def get_user(self, name:str):
        find = self.get_user_raw(name)
        return parse_json(find)
    

    def get_balance(self, name:str):
        return self.get(name, "balance")
    

    def get_savings(self, name:str):
        return self.get(name, "savings")
    

    def get_debt(self, name:str):
        return self.get(name, "debt")
    

    def get_credit(self, name:str):
        return self.get(name, "credit")
    

    def get_transactions(self, name:str):
        return self.get(name, "transactions")
    

    def get_friend_requests(self, name:str):
        return self.get(name, "friend_requests")
    

    def get_friends(self, name:str):
        return self.get(name, "friends")
    

    def get_requests(self, name:str):
        return self.get(name, "requests")
    

    def search_name(self, name:str):
        find = self.users.find_one({"name": name})
        return find != None
    
    
    def search_name_pwd(self, name:str, pwd:str):
        find = self.users.find_one({'name': name, 'pin': pwd})
        return find != None


    def deposit(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc":{"balance": value}})
        self.add_credit(name, value / 5000)


    def withdraw(self, name:str, value:int):
        self.deposit(name, -value)

    
    def pay_debt(self, name:str, value:int):
        self.add_debt(name, -value)

    def pay_request(self, name:str, target:str):
        request = None
        value = -1
        for obj in self.get_requests(name):
            if obj["to"] == name:
                request = request
                value = obj["value"]

        if request is not None:
            balance = self.get_balance(name)
            if balance > value:
                self.send_to(name, target, value)
                self.users.find_one_and_update({"name": name}, {"$pull": {"requests": request}})
                return "Finished transfer!"
            return "Insufficient funds!"
        return f"No request found from {target} to you!"


    
    def send_to(self, name:str, target:str, value:int):
        self.withdraw(name, value)
        self.deposit(target, value)
        self.add_transaction(name, target, value)
        

    def add_debt(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc":{"debt": value * 1.01}})


    def add_savings(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc": {"savings": value * 1.01}})


    def add_transaction(self, name:str, target:str, value:int):
        id = self.transaction_id(date(), name, target, value)
        print(id)
        data_sender = {
            "date": date(),
            "to": target,
            "value": value,
            "hash": id
        }
        data_recv = {
            "date": date(),
            "from": name,
            "value": value,
            "hash": id
        }
        self.users.find_one_and_update({"name": name}, {"$push": {"transactions": data_sender}})
        self.users.find_one_and_update({"name": target}, {"$push": {"transactions": data_recv}})

    
    def clear_transactions(self, name:str):
        find = self.users.find_one_and_update({"name": name}, {"$set": {"transactions": []}})

    
    def clear_database(self):
        self.users.delete_many({})

    
    def transaction_id(self, date:str, name:str, target:str, value:str):
        data = f"{date} {name} {target} {value}"
        hash_object = hashlib.md5(data.encode("utf-8"))
        return hash_object.hexdigest()
    

    def change(self, name:str, operation:str, target_field:str, new_value:str):
        obj = self.get(name, target_field)
        if isinstance(obj, int):
            new_value = int(new_value)

        account = self.users.find_one_and_update({"name": name}, {operation: {target_field: new_value}})

def date():
    return datetime.datetime.today().strftime('%Y-%m-%d')


def parse_json(data):
    return json_util.dumps(data)