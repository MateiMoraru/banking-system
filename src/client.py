import socket
import getpass
import sys

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

    
    def connect(self):
        self.socket.connect(self.server_addr)
        print(f"Connected to host {self.server_addr}")

        signup = input("Do you want to create an account? yes/no\n")
        self.send(signup)
        if signup == "yes":
           self.signup()
           self.login()
        else:
           self.login()

        self.run()


    def run(self):
        while True:
            print()
            data = input(">")
            self.send(data)
            resp = self.recv()
            self.process_recv(resp)

            if "Do you want to add the difference to your debt" in resp:
                ans = input("")
                self.send(ans)
                resp = self.recv()
                self.process_recv(resp)

    
    def signup(self):
        name = input("Name: ")
        password = getpass.getpass(prompt="Password: ")
        credentials = name + ' ' + password
        self.send(credentials)

        confirmation = self.recv()
        if "No password provided" in confirmation:
            print(confirmation)
            self.signup()
        elif "Account already exists" in confirmation:
            print(f"{confirmation}, try again")
            self.signup()
        else:
            print(confirmation)
        print("Please login again")

        
    def login(self):
        name = input("Name: ")
        password = getpass.getpass(prompt="Password: ")
        credentials = name + ' ' + password
        print()

        self.send(credentials)
        confirmation = self.recv()
        if "No password provided" in confirmation:
            print(confirmation)
            self.login()
        elif confirmation == "Wrong credentials":
            print("The credentials you entered weren't found in our database.\n Try again.\n")
            self.login()
        elif "Logged in successfully" in confirmation:
            self.recv()
            print(f"Logged in successfully.")
        elif confirmation == "Account not recognised":
            print("\n Your account was not found in our database.\n Try creating one.\n")


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
        if '-w' in response:
            response = response[0:len(response) - 2]
            print(response)


    def recv(self):
        try:
            message = self.socket.recv(self.BUFFER_SIZE).decode(self.ENCODING)
            return message
        except TimeoutError as e:
            print("Timed out.")
            self.send("shutdown")


if __name__ == "__main__":
    client = Client("127.0.0.1", 8080)
    client.connect()