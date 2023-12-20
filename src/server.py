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
            elif command[0] == "deposit":
                self.handle_deposit(conn, name, command)
            elif command[0] == "withdraw":
                self.handle_withdraw(conn, name, command)
            elif command[0] == "send":
                self.handle_send(conn, name, command)
            elif command[0] == "pay-debt":
                self.handle_pay_debt(conn, name)
            elif command[0] == "loan":
                self.handle_loan(conn, name, command)
            elif command[0] == "get-balance":
                self.handle_get_balance(conn, name)
            elif command[0] == "get-debt":
                self.handle_get_debt(conn, name)
            elif command[0] == "get-data":
                self.get_handle_data(conn, name)
            elif command[0] == "get-data-pretty":
                self.get_handle_data_pretty(conn, name)
            elif command[0] == "help":
                self.help(conn)
            else:
                self.send(conn, 'Unknown command, try running "-h"-w')
            
            print(f"User {name} sent command: {command}")


    def handle_deposit(self, conn:socket.socket, name:str, command:List[int]):
        try:
            value = int(command[1])
        except:
            self.send('Wrong arguments for command, expected "deposit <value>"-w')
            return
        self.database.deposit(name, value)
        balance = self.database.get_balance(name)
        self.send(conn, f"Your current balance has been increased to {balance}-w")


    def handle_withdraw(self, conn:socket.socket, name:str, command:List[int]):
        try:
            value = int(command[1])
        except:
            self.send('Wrong arguments for command, expected "withdraw <value>"-w')
            return
                
        balance = self.database.get_balance(name)
        if balance < value:
            self.send(conn, f"You have insufficient funds\nDo you want to add the difference to your debt? yes/no\n-w")
            resp = self.recv()
            if resp == 'yes':
                self.database.add_debt(name, value - balance)
            else:
                return
        self.database.withdraw(name, balance)
        balance = self.database.get_balance(name)
        self.send(conn, f"Your current balance has been decreased to {balance}-w")


    def handle_send(self, conn:socket.socket, name:str, command:List[str, int]):
        try:
            account = command[1]
            value = int(command[2])
        except:
            self.send('Wrong arguments for command, expected "send <account-name> <value>"-w')
            return

        check = self.database.search_name(account)
        current_balance = self.database.get_balance(name)
        debt = False
        if value > current_balance:
            self.send(conn, "Transfer failed due to insufficient funds\nDo you want to add the difference to your debt? yes/no\n-w")
            resp = self.recv(conn)
            if resp == "yes":
                self.database.add_debt(name, value - current_balance)
                debt = True
            else:
                return
        if check:
            
            if debt:
                value = current_balance
            self.database.send_to(name, account, value)
            self.send(conn, "Transfer finished-w")
        else:
            self.send(conn, f"User {account} doesn't exists-w")


    def handle_pay_debt(self, conn:socket.socket, name:str, command:List[int]):
        debt = self.database.get_debt(name)
        try:
            value = command[1]
            if value == '*' or value == 'all':
                value = debt
            else:
                value = int(value)
        except:
            self.send(conn, 'Wrong arguments for command, expected "pay-debt <value>"-w')
            return
                
        balance = self.database.get_balance(name)
        if debt <= 0:
            self.send(conn, "You don't have any debts-w")
        if balance < value:
            self.send(conn, "You have insufficient funds. Try depositing first-w")
            return
        elif value > debt:
            value = debt
            self.send(conn, f"The amount specified is greater than you total debt, changed the amount to {debt}-w")
                    
        self.database.pay_debt(name, value)
        self.database.add_credit(name, value // 100)
        self.send(conn, f"Your current debt is: {self.database.get_debt(name)}-w")
    

    def handle_loan(self, conn:socket.socket, name:str, command:List[int, str]):
        try:
            value = int(command[1])
            months = int(command[2])
        except:
            self.send(conn, 'Wrong arguments for command, expected "loan <value> <months>"')
                
        credit = self.database.get_credit(name)
        required_credit = months * 50 * value / 10000
        if credit > required_credit:
            self.database.add_debt(name, value)
            self.database.deposit(name, value)
            self.send(conn, f"Loan accepted. You have {months} to pay it back")
        else:
            self.send(conn, f"Load not accepted due to insuficient credit. Required credit: {required_credit}")


    def handle_get_debt(self, conn:socket.socket, name:str):
        debt = self.database.get_debt(name)
        self.send(conn, f"Your current debt is: {debt}-w")


    def handle_get_data(self, conn:socket.socket, name:str):
        data = self.database.get_user(name)
        print(data)
        self.send(conn, f"Current cursor object: \n {data}-w")


    def handle_get_data_pretty(self, conn:socket.socket, name:str):
        data = ""
        user = self.database.get_user_raw(name)
        data += f"Name: {user["name"]}\n"
        data += f"Balance: {user["balance"]}\n"
        data += f"Debt: {user["debt"]}\n"
        data += f"Credit: {user["credit"]}\n"
        self.send(conn, data + "-w")


    def help(self, conn:socket.socket):
        commands = ""
        commands += "deposit <value> -> deposits the value specified in your account\n"
        commands += "withdraw <value> -> withdraws the value specified from you account\n"
        commands += "pay-debt <value> -> removes the value specified from your account's debt\n"
        commands += "send <name> <value> -> sends the value specified to the account specified\n"
        commands += "loan <value> <months> -> loans you money if you have enough credit\n"
        commands += "get-balance -> returns your balance\n"
        commands += "get-data -> returns your account's data\n"
        commands += "get-data-pretty -> returns your data in a more readable manner\n"
        commands += "shutdown -> shuts down server\n-w"
        self.send(conn, commands)


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