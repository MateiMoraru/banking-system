import database
import sys
import threading
import time
from typing import Tuple, List
import socket

class Server:
    BUFFER_SIZE = 4096
    ENCODING = "UTF-8"

    def __init__(self, ip:str="127.0.0.1", port:int=8080):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (ip, port)
        self.database = database.Mongo()
        self.listening = True
        self.connections = []


    def run(self):
        self.socket.bind(self.addr)
        self.socket.listen()
        print(f"Server is listening for connections on {self.addr}.")
        
        while self.listening:
            conn, addr = self.socket.accept()
            print(f"Client connected from {addr}")
            self.connections.append(conn)
            try:    
                client = threading.Thread(target=self.handle_conn, args=[conn])
                client.start()
                for connection in self.connections:
                    self.send(connection, "New connection established.")
            except Exception as e:
                print(e)
                print("Client disconnected")
                self.shutdown(conn)
    

    def handle_conn(self, conn: socket.socket):
        name = None
        signup = self.recv(conn)
        
        if signup == 'yes':
            self.signup(conn)
            name = self.login(conn)
            print(name)
        else:
            name = self.login(conn)
            print(name)
        if name == False:
            self.send(conn, "shutdown")
        else:
            self.send(conn, "logged in")

        try:
            self.loop(conn, name)
        except Exception as e:
            print(e)
            self.shutdown()


    def loop(self, conn:socket.socket, name:str):
        print(name)
        while True:
            command = self.recv(conn).split(' ')
            if command[0] == "shutdown":
                self.shutdown()
            elif command[0] == "balance":
                balance = self.database.get_balance(name)
                print(f"Your current balance is: {balance}-w")
                self.send(conn, f"Your current balance is: {balance}-w")
            elif command[0] == "deposit":
                try:
                    value = int(command[1])
                except:
                    self.send('Wrong arguments for command, expected "deposit <value>"-w')
                    break
                self.database.deposit(name, value)
                balance = self.database.get_balance(name)
                self.send(conn, f"Your current balance has been increased to {balance}-w")
            elif command[0] == "withdraw":
                try:
                    value = int(command[1])
                except:
                    self.send('Wrong arguments for command, expected "withdraw <value>"-w')
                    break
                self.database.withdraw(name, value)
                balance = self.database.get_balance(name)
                self.send(conn, f"Your current balance has been decreased to {balance}-w")
            elif command[0] == "send":
                argvs = []
                try:
                    argvs.append(command[1])
                    argvs.append(int(command[2]))
                except:
                    self.send('Wrong arguments for command, expected "send <account-name> <value>"-w')
                    break

                check = self.database.search_name(argvs[0])
                current_balance = int(self.database.get_balance(name))
                debt = False
                if argvs[1] > current_balance:
                    self.send(conn, "Transfer failed due to insufficient funds\nDo you want to add the difference to your debt? yes/no\n-w")
                    resp = self.recv(conn)
                    if resp == "yes":
                        self.database.add_debt(name, argvs[1] - current_balance)
                        debt = True
                    else:
                        break
                if check:
                    
                    if debt:
                        argvs[1] = current_balance
                    self.database.send_to(name, argvs[0], argvs[1])
                    self.send(conn, "Transfer finished-w")
                else:
                    self.send(conn, f"User {argvs[0]} doesn't exists-w")
                
            elif command[0] == "get-data":
                data = self.database.get_user(name)
                print(data)
                self.send(conn, data + '-w')
            
            print(command)


    def signup(self, conn: socket.socket):
        credentials = self.recv(conn)
        name = credentials.split(' ')[0]
        password = credentials.split(' ')[1]
        if len(password) < 1:
            print("No password provided")
            self.send(conn, "No password provided-w")
            self.signup(conn)

        
        if self.database.search_name(name):
            self.send(conn, "Account already exists-w")
            self.signup(conn)
        else:
            self.database.add_user(name, password, "user")
            self.send(conn, "Account created successfully-w")


    def login(self, conn: socket.socket, count: int = 0):
        print("Login")
        credentials = self.recv(conn)
        name = credentials.split(' ')[0]
        password = credentials.split(' ')[1]
        if len(password) < 1:
            print("No password provided")
            self.send(conn, "No password provided")
            self.login(conn)
        
        resp = self.database.search_name_pwd(name, password)

        if count <= 2 and resp is None:
            self.send(conn, "Wrong credentials-w")
            return
        if resp:
            self.send(conn, "Logged in successfully-w")
            return name
        
        self.send(conn, "Account not recognised-w")
        return False


    def shutdown(self):
        print(f"Shutting down server")
        self.listening = False
        self.socket.close()
        sys.exit(0)


    def send(self, conn: socket.socket, message: str):
        bytes_all = message.encode(self.ENCODING)
        bytes_sent = conn.send(bytes_all)

        if bytes_all != bytes_sent:
            return False
        
        return True
    
    def recv(self, conn: socket.socket):
        try:
            message = conn.recv(self.BUFFER_SIZE).decode(self.ENCODING)
            return message
        except TimeoutError as e:
            print(e)

if __name__ == "__main__":
    server = Server()
    server.run()