import pymongo
from typing import List
import json
from bson import json_util

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


    def add_user(self, name:str, password:str, rights:str):
        data = {
            "name": name, 
            "password": password, 
            "balance": 0,
            "economy": 0,
            "debt": 0,
            "credit": 0
            }
        self.users.insert_one(data)

    
    def get_user(self, name:str):
        find = self.users.find_one({"name": name})
        return parse_json(find)
    

    def search_name(self, name:str):
        find = self.users.find_one({"name": name})
        print(find)
        return find != None
    
    
    def search_name_pwd(self, name:str, pwd:str):
        find = self.users.find_one({'name': name, 'password': pwd})
        return find != None
    

    def get_balance(self, name:str):
        find = self.users.find_one({"name": name})
        if find:
            return str(find["balance"])
        return None
    

    def deposit(self, name:str, value:int):
        find = self.users.find_one_and_update({"name": name}, {"$inc":{"balance": value}})


    def withdraw(self, name:str, value:int):
        self.deposit(name, -value)

    
    def pay_debt(self, name:str, value:int):
        pass

    
    def send_to(self, name:str, target:str, value:int):
        self.withdraw(name, value)
        self.deposit(target, value)
        

    def add_debt(self, name:str, value:int):
        find = self.users.find_one_and_update({"name": name}, {"$inc":{"debt": value}})
