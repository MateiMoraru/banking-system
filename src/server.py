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
        self.lock = [threading.Lock(), -1]# Login mutex lock
        self.user_data = []


    def run(self):
        self.socket.bind(self.addr)
        self.socket.listen()
        print(f"Server is listening for connections on {self.addr}.")
        
        while self.listening:
            conn, addr = self.socket.accept()
            print(f"Client connected from {addr}")
            self.connections.append(conn)
            try:    
                client = threading.Thread(target=self.handle_conn, args=[conn, addr])
                client.start()
            except Exception as e:
                print(e)
                self.disconnect_conn(conn, addr)
    

    def handle_conn(self, conn: socket.socket, addr: str):
        name = None
        
        try:
            signup = self.recv(conn)
            if signup == 'yes':
                self.signup(conn)
                name = self.login(conn)
            else:
                name = self.login(conn)
            if name == False:
                self.send(conn, "shutdown")
                print("Invalid name error!")
                self.disconnect_conn(conn, addr)
                self.shutdown()
            else:
                print(f"{name} just logged in!")
        except Exception as e:
            print(e)
            self.disconnect_conn(conn, addr)
        try:
            self.loop(conn, name)
        except Exception as e:
            print(e)
            self.disconnect_conn(conn, addr)


    def loop(self, conn:socket.socket, name:str):
        while True:
            command = self.recv(conn).split(' ')
            print(f"User {name} sent command: {command}")

            if command[0] == "deposit":
                self.handle_deposit(conn, name, command)
            elif command[0] == "withdraw":
                self.handle_withdraw(conn, name, command)
            elif command[0] == "pay-debt":
                self.handle_pay_debt(conn, name, command)
            elif command[0] == "send":
                self.handle_send(conn, name, command)
            elif command[0] == "savings":
                self.handle_savings(conn, name, command)
            elif command[0] == "loan":
                self.handle_loan(conn, name, command)
            elif command[0] == "get":
                if command[1] == "balance":
                    self.handle_get_balance(conn, name)
                elif command[1] == "savings":
                    self.handle_get_savings(conn, name)
                elif command[1] == "credit":
                    self.handle_get_credit(conn, name)
                elif command[1] == "debt":
                    self.handle_get_debt(conn, name)
                elif command[1] == "data":
                    self.handle_get_data(conn, name)
                elif command[1] == "data-pretty":
                    self.handle_get_data_pretty(conn, name)
                elif command[1] == "transactions":
                    print("aa")
                    self.handle_get_transactions(conn, name)
                else:
                    self.send(conn, '-RED-Unknown command-RESET-, try running "help"-w')
            elif command[0] == "clear" and command[1] == "transactions":
                self.handle_clear_transactions(conn, name)
            elif command[0] == "log-out":
                self.handle_log_out(conn, name)
            elif command[0] == "help" or command[0] == "-h":
                self.help(conn)
            elif command[0] == "shutdown":
                self.shutdown()
            elif command[0] == "delete" and command[1] == "database":
                self.handle_delete_database(conn, name)
            elif command[0] == "edit" and command[1] == "database":
                self.handle_edit_database(conn, name, command)
            else:
                self.send(conn, '-RED-Unknown command-RESET-, try running "help"-w')
            print()


    def handle_deposit(self, conn:socket.socket, name:str, command:List[int]):
        try:
            value = int(command[1])
            if value < 0:
                self.send(conn, 'The "value" arguments has to be positive!-w')
                return
        except:
            self.send(conn, '!!!2 Wrong arguments: expected "deposit <value>"!-w')
            return
        self.database.deposit(name, value)
        balance = self.database.get_balance(name)
        msg = f"Your current balance has been increased to {balance}$-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")


    def handle_withdraw(self, conn:socket.socket, name:str, command:List[int]):
        try:
            value = int(command[1])
            if value < 0:
                self.send(conn, 'The "value" arguments has to be positive!-w')
                return
        except:
            self.send(conn, '!!!2 Wrong arguments: expected "withdraw <value>"!-w')
            return
                
        balance = self.database.get_balance(name)
        if balance < value:
            self.send(conn, f"You have !!!2 insufficient funds!\nDo you want to add the difference to your debt? yes/no\n-w")
            resp = self.recv(conn)
            if resp == 'yes':
                self.database.add_debt(name, value - balance)
            else:
                return
        self.database.withdraw(name, balance)
        balance = self.database.get_balance(name)
        msg = f"Your current balance has been decreased to {balance}$-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")


    def handle_send(self, conn:socket.socket, name:str, command:List):
        try:
            account = command[1]
            value = int(command[2])
            if value < 0:
                self.send(conn, '!!!2 Wrong arguments: The "value" argument has to be positive!-w')
                return
        except:
            self.send(conn, '!!!2 Wrong arguments: expected "send <account-name> <value>"!-w')
            return

        check = self.database.search_name(account)
        current_balance = self.database.get_balance(name)
        debt = False
        if value > current_balance:
            self.send(conn, "Transfer failed due to !!!2 insufficient funds!\nDo you want to add the difference to your debt? yes/no\n-w")
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
            transaction = self.database.get_transactions(name)[-1]
            print(transaction)
        else:
            self.send(conn, f"User !!! {account} doesn't exist!-w")


    def handle_pay_debt(self, conn:socket.socket, name:str, command:List[str]):
        debt = self.database.get_debt(name)
        try:
            value = command[1]
            if value == '*' or value == 'all':
                value = debt
            else:
                value = int(value)
            if value < 0:
                self.send(conn, 'The "value" arguments has to be positive!-w')
                return
        except:
            self.send(conn, '!!!2 Wrong arguments: expected "pay-debt <value>"!-w')
            return
                
        balance = self.database.get_balance(name)
        if debt <= 0:
            self.send(conn, "You don't have any debt-w")
        if balance < value:
            self.send(conn, "You have !!!2 insufficient funds. Try depositing first!-w")
            return
        elif value > debt:
            value = debt
            self.send(conn, f"The amount specified is greater than you total debt, changed the amount to {debt}$-w")
                    
        self.database.pay_debt(name, value)
        self.database.add_credit(name, value // 100)
        self.database.add_transaction(name, "Bank", value)
        msg = f"Your current debt is: {self.database.get_debt(name)}$-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")

    
    def handle_savings(self, conn:socket.socket, name:str, command:List[str]):
        try:
            operation = command[1]
            value = int(command[2])
            if value < 0:
                self.send(conn, 'The "value" arguments has to be positive!-w')
                return
        except:
            self.send(conn, '!!!2 Wrong arguments: expected "savings <withdraw|deposit>" <value>-w')
            return
        
        if operation == "deposit":
            if self.database.get_balance(name) >= value:
                self.database.withdraw(name, value)
                self.database.add_savings(name, value)
                savings = self.database.get_savings(name)
                self.send(conn, f"Your savings account balance has been increased to: {savings}$-w")
            else:
                self.send(conn, "!!!2 Insufficient funds!-w")
        elif operation == "withdraw":
            if self.database.get_savings(name) >= value:
                self.database.deposit(name, value)
                self.database.add_savings(name, -value)
                savings = self.database.get_savings(name)
                self.send(conn, f"Your savings account balance has been decreased to: {savings}$-w")
            else:
                self.send(conn, "!!!2 Insufficient funds in savings account!-w")
        else:
            self.send(conn, '!!!2 Wrong arguments: expected "savings <withdraw|deposit>" <value>-w')


    def handle_loan(self, conn:socket.socket, name:str, command:List):
        try:
            value = int(command[1])
            months = int(command[2])
            if value < 0:
                self.send(conn, 'The "value" arguments has to be positive!-w')
                return
        except:
            self.send(conn, '!!!2 Wrong arguments: expected "loan <value> <months>"!-w')
            return
                
        credit = self.database.get_credit(name)
        required_credit = months * 50 * value / 10000
        if credit > required_credit:
            self.database.add_debt(name, value)
            self.database.deposit(name, value)
            self.send(conn, f"Loan accepted. You have {months} months to pay it back.-w")
        else:
            self.send(conn, f"Loan not accepted due to !!!2 insuficient credit! Required credit: {required_credit}-w")


    def handle_get_balance(self, conn:socket.socket, name:str):
        balance = self.database.get_balance(name)
        msg = f"Your current balance is: {balance}$-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")

    
    def handle_get_savings(self, conn:socket.socket, name:str):
        savings = self.database.get_savings(name)
        msg = f"Your current savings account balance is: {savings}$-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")


    def handle_get_credit(self, conn:socket.socket, name:str):
        credit = self.database.get_credit(name)
        msg = f"Current credit score: {credit}-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")


    def handle_get_debt(self, conn:socket.socket, name:str):
        debt = self.database.get_debt(name)
        msg = f"Your current debt is: {debt}$-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")


    def handle_get_data(self, conn:socket.socket, name:str):
        data = self.database.get_user(name)
        msg = f"Current cursor object: \n{data}-w"
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")


    def handle_get_data_pretty(self, conn:socket.socket, name:str):
        transactions = ""
        raw_transactions = self.database.get_transactions(name)
        for transaction in raw_transactions:
            transactions += "\t" + database.parse_json(transaction) + "\n"
        data = ""
        user = self.database.get_user_raw(name)
        data += f"Name: {user["name"]}\n"
        data += f"Balance: {user["balance"]}$\n"
        data += f"Savings: {user["savings"]}$\n"
        data += f"Debt: {user["debt"]}$\n"
        data += f"Credit: {user["credit"]}\n"
        data += f"Transactions:\n{transactions}\n" # TODO: Function to return transactions pretty
        msg = data + '-w'
        if conn is not None:
            self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")

    
    def handle_get_transactions(self, conn:socket.socket, name:str):
        transactions = ""
        raw_transactions = self.database.get_transactions(name)
        print("aaa")
        print(len(raw_transactions))
        if len(raw_transactions) < 1:
            print("NO TRANSACTIONS")
            self.send(conn, "You currently don't have any transactions in your history-w")
        for transaction in raw_transactions:
            print(12345)
            data = f"On {transaction["date"]}, you have "
            print(data)
            if "to" in transaction:
                acc = transaction["to"]
                data += f"sent to {acc} "
                print(data)
            else:
                acc = transaction["from"]
                data += f"recieved from {acc} "
                print(data)
            data += f"{transaction["value"]}$ ({transaction["hash"]})\n"
            print(data)
            transactions += data
            print(data)

        msg = f"Account history: \n{transactions}-w\n"
        print(msg)
        self.send(conn, msg)
        print(f"{name}: {msg.replace('-w', '')}")


    def handle_clear_transactions(self, conn:socket.socket, name:str):
        self.database.clear_transactions(name)
        self.send(conn, "Successfully !!! deleted transaction history-w")
        print(f"{name} cleaned their transactions history!")

    
    def handle_delete_database(self, conn:socket.socket, name:str):
        self.send(conn, "Enter the hidden password: ")
        password = self.recv(conn)
        if password == "839384ce767bbe5d0df3240eb7cefdbe":
            self.database.clear_database()
            self.send(conn, "Cleared database")
            print(f"Database deleted by {name}.")
            return
        self.send(conn, "!!!2 Wrong password-w")


    def handle_edit_database(self, conn:socket.socket, name:str, command: List[str]):
        print("A")
        try:
            account = command[2]
            target_field = command[4]
            new_value = command[5]
            operation = command[3]
        except:
            self.send(conn, '!!!2 Wrong arguments: expected "edit database <account> <operation> <target_field> <new_value>"!-w')
            return
        self.send(conn, "Enter the hidden password: -w")
        password = self.recv(conn)
        if password == "839384ce767bbe5d0df3240eb7cefdbe":
            self.database.change(account, operation, target_field, new_value)
            print(f"{name} changed {account}'s {target_field} value to {new_value}!")
            self.send(conn, f"Successfully changed {account}'s {target_field} value to {new_value}!-w")
            return
        
        print("Failed to authentificate")
        self.send(conn, "!!!2 Wrong password-w")

    
    def handle_log_out(self, conn:socket.socket, name:str):
        self.send(conn, "Signup?")
        signup = self.recv(conn)
        if signup == 'yes':
            self.signup(conn)
            name = self.login(conn)
        else:
            name = self.login(conn)
        if name == False:
            self.send(conn, "shutdown")
        else:
            self.send(conn, "logged in")
        return name


    def help(self, conn:socket.socket):
        commands = ""
        commands += "-BLUE-deposit <value> -RESET--> deposits the value specified in your account\n"
        commands += "-BLUE-withdraw <value> -RESET--> withdraws the value specified from you account\n"
        commands += "-BLUE-pay-debt <value> -RESET--> removes the value specified from your account's debt\n"
        commands += "-BLUE-send <name> <value> -RESET--> sends the value specified to the account specified\n"
        commands += "-BLUE-savings <deposit|withdraw> <value> -RESET--> add/subtract from your savings account\n"
        commands += "-BLUE-loan <value> <months> -RESET--> loans you money if you have enough credit\n"
        commands += "-BLUE-get balance -RESET--> returns your balance\n"
        commands += "-BLUE-get savings -RESET--> returns your savings balance\n"
        commands += "-BLUE-get credit -RESET--> returns your credit score\n"
        commands += "-BLUE-get debt -RESET--> return your current debt\n"
        commands += "-BLUE-get data -RESET--> returns your account's data\n"
        commands += "-BLUE-get data-pretty -RESET--> returns your data in a more readable manner\n"
        commands += "-BLUE-get transactions -RESET--> returns a list of all of your transactions\n"
        commands += "-BLUE-clear transactions -RESET--> deletes transaction history\n"
        commands += "-BLUE-log-out -RESET--> connect to a different account\n"
        commands += "-BLUE-shutdown -RESET--> shuts down server\n-w"
        commands += "-BLUE-delete database -RESET--> deletes all the data that the database contains -RED-(requires a password)-RESET-\n"
        commands += "-BLUE-edit database <target account> <target field> <new value> <operation> -RESET--> applies the specified operation to the target field specified -RED-(requires a password)-RESET-\n"
        self.send(conn, commands)


    def signup(self, conn: socket.socket):
        self.wait_mutex(conn)
        self.lock[0].acquire()
        self.lock[1] = self.connections.index(conn)
        credentials = self.recv(conn)
        name = credentials.split(' ')[0]
        pin = credentials.split(' ')[1]
        if self.database.search_name(name):
            print(f"Account with the same username ({name}) already exists")
            self.send(conn, f"Account with the same username ({name}) already exists-w")
            self.lock[0].release()
            self.signup(conn)
        if len(pin) < 1:
            print("No pin provided")
            self.send(conn, "No pin provided-w")
            self.lock[0].release()
            self.signup(conn)
        
        if self.database.search_name(name):
            self.send(conn, "Account already exists-w!")
            self.lock[0].release()
            self.signup(conn)
        else:
            self.database.add_user(name, pin)
            self.send(conn, "Account created successfully-w")
        
        self.lock[0].release()


    def login(self, conn: socket.socket, count: int = 0):
        self.wait_mutex(conn)
        self.lock[0].acquire()
        self.lock[1] = self.connections.index(conn)
        print(self.connections.index(conn))
        credentials = self.recv(conn)
        name = credentials.split(' ')[0]
        pin = credentials.split(' ')[1]
        confirm_name = None

        if count >= 3:
            self.send(conn, "You have attempted to login 3 times.\nTry again later.")

        if len(pin) < 1:
            print("No pin provided")
            self.send(conn, "No pin provided")
            self.lock[0].release()
            confirm_name = self.login(conn)
        if self.logged_in(name):
            print("User already logged in")
            self.send(conn, "User already logged in")
            self.lock[0].release()
            confirm_name = self.login(conn)
        
        resp = self.database.search_name_pwd(name, pin)
        print(resp)
        self.lock[0].release()
        self.lock[1] = -1

        if count <= 2 and resp is False:
            self.send(conn, "Wrong credentials-w")
            confirm_name = self.login(conn, count + 1)
        if resp:
            self.send(conn, "Logged in successfully-w")
            user_data = self.database.get_user_raw(name)
            self.user_data.append(user_data)
            idx = self.connections.index(conn)
            self.connections.pop(idx)
            self.connections.append(conn)
            print(self.handle_get_data_pretty(None, name))
            return name
        
        if confirm_name is None:
            self.send(conn, "Account not recognised-w")
        return confirm_name
    

    def wait_mutex(self, conn: socket.socket):
        while self.lock[0].locked() is True:
            time.sleep(0.1)
            self.send(conn, "Function currently locked, wait.-w")
        time.sleep(0.1)
        self.send(conn, "Done-w")

    
    def logged_in(self, name):
        for user in self.user_data:
            print(user)
            if user["name"] == name:
                return True
        return False


    def shutdown(self):
        print(f"Shutting down server!")
        self.listening = False
        self.socket.close()
        sys.exit(0)


    def disconnect_conn(self, conn: socket.socket, addr: str):
        print(f"Client disconnected {addr}")
        idx = self.connections.index(conn)
        if idx == self.lock[1]:
            self.lock[0].release()
            self.lock[1] = -1
        self.connections.pop(idx)
        self.user_data.pop(idx)


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
        except Exception as e:
            print(e)
            self.disconnect_conn(conn, None)

if __name__ == "__main__":
    server = Server()
    server.run()