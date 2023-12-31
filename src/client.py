import hashlib
import socket
import getpass
import sys
from colorama import *

class Client:
    ENCODING = "UTF-8"
    BUFFER_SIZE = 4096

    def __init__(self, ip: str = "127.0.0.1", port: int = 8080):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)
        self.server_addr = (ip, port)

        self.user_name = "None"
        self.user_rights = "None"
        self.path = ""
        init() # From colorama

    
    def connect(self):
        self.socket.connect(self.server_addr)
        print(f"Connected to host {self.server_addr}")

        self.handle_log_out()
        friend_data = self.recv()
        self.process_recv(friend_data)
        friend_request_data = self.recv()
        self.process_recv(friend_request_data)
        try:
            self.run()
        except Exception as e:
            print(f"ERROR: {e}")
            self.shutdown()


    def run(self):
        while True:
            print()
            data = input(">")
            self.send(data)
            resp = self.recv()
            self.process_recv(resp)

            if "Do you want to add the difference to your debt" in resp:
                self.handle_add_to_debt(self)
            elif "Signup?" in resp:
                self.handle_log_out()
            elif "password: " in resp:
                self.handle_get_password(resp)
                

    def handle_add_to_debt(self):
        ans = input("")
        self.send(ans)
        resp = self.recv()
        self.process_recv(resp)

    
    def handle_get_password(self, resp: str):
        password = input()
        self.send(self.hash(password))
        resp = self.recv()
        self.process_recv(resp)


    def handle_log_out(self):
        signup = input("Do you want to create an account? yes/no\n")
        self.send(signup)
        if signup == "yes":
           self.signup()
           self.login()
        else:
           self.login()

    
    def signup(self):
        try:
            self.wait_mutex()
        except TypeError as e:
            print(f"{Fore.RED}ERROR: failed to receieve mutex confirmation")
        name = input("Name: ")
        pin = getpass.getpass(prompt="pin: ")
        while len(pin) != 4:
            print("Please insert a pin such as: 1234")
            pin = getpass.getpass(prompt="pin: ")
        pin = self.hash(pin)
        credentials = name + ' ' + pin
        self.send(credentials)

        confirmation = self.recv()
        if "No pin provided" in confirmation:
            print(confirmation)
            self.signup()
        elif "already exists" in confirmation:
            self.process_recv(confirmation)
            self.signup()
        elif "Account already exists" in confirmation:
            print(f"{confirmation}, try again")
            self.signup()
        else:
            self.process_recv(confirmation)
        print("Please login again")

        
    def login(self):
        self.wait_mutex()            
        name = input("Name: ")
        pin = getpass.getpass(prompt="pin: ")
        while len(pin) != 4:
            print("Please insert a pin such as: 1234")
            pin = getpass.getpass(prompt="pin: ")
        pin = self.hash(pin)
        credentials = name + ' ' + pin
        print()

        self.send(credentials)
        confirmation = self.recv()
        if "No pin provided" in confirmation:
            print(confirmation)
            self.login()
        elif "already logged in" in confirmation:
            print(confirmation)
            self.login()
        elif "Wrong credentials" in confirmation:
            print("The credentials you entered weren't found in our database.\nTry again.")
            self.login()
        elif "Logged in successfully" in confirmation:
            print(f"Logged in successfully.")
        elif confirmation == "Account not recognised":
            print("\n Your account was not found in our database.\nTry creating one.")

    def wait_mutex(self):
        mutex = self.recv()
        if 'Done' not in mutex:
            print("Wait, the function is currently being used by an other account.") 
        while 'Done' not in mutex:
            mutex = self.recv()    
        print("Acquired lock")


    def shutdown(self):
        print("Shutting down client.")
        self.socket.close()
        sys.exit(0)


    def send(self, message: str):
        bytes_all = message.encode(self.ENCODING)
        bytes_sent = self.socket.send(bytes_all)

        if bytes_all != bytes_sent:
            return False
        return True
    

    def process_recv(self, response:str):
        if '\n' in response:
            responses = response.split('\n')
            for resp in responses:
                self.process_recv(resp + '-w')
            return
        resp_arr = response.split(' ')
        if 'Bank' in response:
            response = response.replace('Bank', Fore.YELLOW + "Bank" + Fore.RESET)
        if '-RED-' in response:
            response = response.replace('-RED-', Fore.RED)
        if '-GREEN-' in response:
            response = response.replace('-GREEN-', Fore.GREEN)
        if '-BLUE-' in response:
            response = response.replace('-BLUE-', Fore.LIGHTBLUE_EX)
        if '-RESET-' in response:
            response = response.replace('-RESET-', Fore.RESET)
        if '-w' in response:
            response = response.replace('-w', Fore.RESET)
            print(response)


    def recv(self):
        try:
            message = self.socket.recv(self.BUFFER_SIZE).decode(self.ENCODING)
            return message
        except TimeoutError as e:
            print("Timed out.")
            self.send("shutdown")


    def hash(self, message: str):
        obj = hashlib.md5(message.encode('utf-8'))
        return obj.hexdigest()

if __name__ == "__main__":
    client = Client("127.0.0.1", 8080)
    client.connect()