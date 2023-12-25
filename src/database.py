import pymongo
from typing import List
from bson import json_util
import datetime
import uuid

def parse_json(data):
    return json_util.dumps(data)

class Mongo:
    def __init__(self, addr:str="mongodb://localhost:27017/"):
        try:
            self.client = pymongo.MongoClient(addr)
            self.client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError as err:
            print(err)

        self.users = self.client["Banking-system"]["clients"]


    def add_user(self, name:str, pin:str, rights:str):
        data = {
            "name": name, 
            "pin": pin, 
            "balance": 0,
            "savings": 0,
            "debt": 0,
            "credit": 0,
            "transactions": []
            }
        self.users.insert_one(data)


    def add_credit(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc":{"credit": value}})


    def get_user_raw(self, name:str):
        find = self.users.find_one({"name": name})
        return find

    
    def get_user(self, name:str):
        find = self.get_user_raw(name)
        return parse_json(find)
    

    def get_balance(self, name:str):
        find = self.users.find_one({"name": name})
        if find:
            return int(find["balance"])
        return None
    

    def get_savings(self, name:str):
        find = self.users.find_one({"name": name})
        if find:
            return int(find["savings"])
        return None
    

    def get_debt(self, name:str):
        find = self.users.find_one({"name": name})
        if find:
            return int(find["debt"])
        return None
    

    def get_debt(self, name:str):
        find = self.users.find_one({"name": name})
        if find:
            return int(find["debt"])
        return None
    

    def get_credit(self, name:str):
        find = self.users.find_one({"name": name})
        if find:
            return int(find["credit"])
        return None
    

    def get_transactions(self, name:str):
        find = self.users.find_one({"name": name})
        if find:
            return find["transactions"]
        return None
    

    def search_name(self, name:str):
        find = self.users.find_one({"name": name})
        print(find)
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

    
    def send_to(self, name:str, target:str, value:int):
        self.withdraw(name, value)
        self.deposit(target, value)
        self.add_transaction(name, target, value)
        

    def add_debt(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc":{"debt": value * 1.01}})


    def add_savings(self, name:str, value:int):
        self.users.find_one_and_update({"name": name}, {"$inc": {"savings": value * 1.01}})


    def add_transaction(self, name:str, target:str, value:int):
        id = self.transaction_id()
        data_sender = {
            "date": date(),
            "to": target,
            "value": value,
            "id": id
        }
        data_recv = {
            "date": date(),
            "from": name,
            "value": value,
            "id": id
        }
        self.users.find_one_and_update({"name": name}, {"$push": {"transactions": data_sender}})
        self.users.find_one_and_update({"name": target}, {"$push": {"transactions": data_recv}})

    
    def clear_transactions(self, name:str):
        find = self.users.find_one_and_update({"name": name}, {"$set": {"transactions": []}})

    
    def transaction_id(self):
        return uuid.uuid1().hex

def date():
    return datetime.datetime.today().strftime('%Y-%m-%d')