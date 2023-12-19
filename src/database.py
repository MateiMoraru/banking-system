import pymongo
from typing import List

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
            "debt": 0,
            "credit": 0
            }
        self.users.insert_one(data)

    def search_name(self, name:str):
        return self.users.find_one({"name": name}) != None
    
    def search_name_pwd(self, name:str, pwd:str):
        return self.users.find({'name': name, 'password': pwd}) != None
    

    def get_balance(self, name:str):
        find = self.users.find_one({'name': name})
        print(find)
        if find:
            print(str(find["balance"]))
            return str(find["balance"])
        return None