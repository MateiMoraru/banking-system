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
        self.file_system = self.client["File-server"]["file-system"]

    def create_repo(self, repo_name:str, user_name:str):
        dict = {
            "name": repo_name,
            "creator": user_name, 
            "collaborators": [user_name], 
            "readers": [user_name]
            }
        self.file_system.insert_one(dict)

    def set_collaborators(self, repo_name:str, collaborators:List[str]):
        for user in collaborators:
            self.file_system.find_one_and_update({"name": repo_name}, {"$push": {"collaborators": user}})

    def set_readers(self, repo_name:str, readers:List[str]):
        self.file_system.find_one_and_update({"name": repo_name}, {"$push": {"readers": readers}})

    def get_readers(self, repo_name:str):
        return self.file_system.find_one({"name": repo_name})["readers"]
    
    def get_collaborators(self, repo_name:str):
        return self.file_system.find_one({"name": repo_name})["collaborators"]

    def add_user(self, name:str, password:str, rights:str):
        data = {
            "name": name, 
            "password": password, 
            "rights": rights
            }
        self.users.insert_one(data)

    def search_name(self, name:str):
        return self.users.find_one({"name": name}) != None
    
    def search_name_pwd(self, name:str, pwd:str):
        return self.users.find({'name': name, 'password': pwd}) != None
    
    def is_admin(self, name:str):
        user = self.users.find_one({"name": name})
        if user == None:
            return None
        return str(user["rights"])
    
    def is_empty(self, name:str):
        return self.users.find_one({"name": name})["password"] == "NotInitialised"
    
    def set_password(self, name:str, password:str):
        user = self.users.find_one({"name": name})
        user.update({"$set": {"password": password}})
    
    def add_empty_user(self, name:str, rights:str="user"):
        data = {"name": name, "password": "NotInitialised", "rights": rights}
        self.users.insert_one(data)