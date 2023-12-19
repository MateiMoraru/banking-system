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
        print(f"Server Listening For Connections on {self.addr}.")
        
        while self.listening:
            conn, addr = self.socket.accept()
            print(f"Client Connected From {addr}")
            self.connections.append(conn)
            try:    
                client = threading.Thread(target=self.handle_conn, args=[conn])
                client.start()
                for connection in self.connections:
                    self.send(connection, "New connection established.")
            except Exception as e:
                print(e)
                print("Client Disconnected")
                self.shutdown(conn)
    

    def handle_conn(self, conn: socket.socket):
        name = "None"
        signup = self.recv(conn)
        
        if signup == 'yes':
            self.signup(conn)
            name = self.login(conn)
        else:
            name = self.login(conn)

        conns = ""
        for i in range(0, len(self.connections)):
            conns += f"{i}. {self.connections[i]}"
            time.sleep(1)
        self.send(conn, conns)

        try:
            self.loop(conn, name)
        except Exception as e:
            print(e)
            self.shutdown()


    def loop(self, conn:socket.socket, name:str):
        while True:
            command = self.recv(conn).split(' ')
            if command[0] == "shutdown":
                self.shutdown()
            elif command[0] == "balance":
                balance = self.database.get_balance(name)
                print(balance)
                self.send(conn, str(balance))
            print(command)


    def signup(self, conn: socket.socket):
        credentials = self.recv(conn)
        name = credentials.split(' ')[0]
        password = credentials.split(' ')[1]
        if len(password) < 1:
            print("No Password Provided")
            self.send(conn, "No Password Provided-w")
            self.signup(conn)

        
        if self.database.search_name(name):
            self.send(conn, "Account Already Exists-w")
            self.signup(conn)
        else:
            self.database.add_user(name, password, "user")
            self.send(conn, "Account Created Successfully-w")


    def login(self, conn: socket.socket, count: int = 0):
        print("Login")
        credentials = self.recv(conn)
        name = credentials.split(' ')[0]
        password = credentials.split(' ')[1]
        if len(password) < 1:
            print("No Password Provided")
            self.send(conn, "No Password Provided")
            self.login(conn)
        
        resp = self.database.search_name_pwd(name, password)

        if count <= 2 and resp is None:
            self.send(conn, "Wrong Credentials-w")
            return
        if resp:
            self.send(conn, "Logged In Successfully-w")
            return
        
        self.send(conn, "Account Not Recognised-w")
        return False


    def shutdown(self):
        print(f"Shutting Down Server")
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