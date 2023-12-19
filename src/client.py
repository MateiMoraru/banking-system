import socket
import getpass

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

        signup = input("Do You Want To Create An Account? yes/no\n")
        self.send(signup)

        if signup == "yes":
           self.signup()
           self.login()
        else:
           self.login()

        self.run()


    def run(self):
        conns = self.recv()
        print(conns)
        
        while True:
            data = input(">")

            print(data)

    
    def signup(self):
        username = input("Username: ")
        password = getpass.getpass(prompt="Password: ")
        credentials = username + ' ' + password

        self.send(credentials)

        confirmation = self.recv()

        if "No Password Provided" in confirmation:
            print(confirmation)
            self.signup()
        elif "Account Already Exists" in confirmation:
            print(f"{confirmation}, Try Again")
            self.signup()

        else:
            print(confirmation)

        print("Please Login Again\n")

        
    def login(self):
        username = input("Username: ")
        password = getpass.getpass(prompt="Password: ")
        credentials = username + ' ' + password
        print()

        self.send(credentials)
        confirmation = self.recv()
        if "No Password Provided" in confirmation:
            print(confirmation)
            self.login()
        elif "Welcome" in confirmation:
            confirmation = self.recv()
            self.process_recv(confirmation)
        elif "Logged In Successfully" in confirmation:
            self.user_rights = self.recv()
            self.user_name = username
            print(f"Logged In Successfully, With {self.user_rights} Rights.\n")
        elif confirmation == "Wrong Credentials":
            print("The Credentials You Entered Weren't Found In Our Database.\n Try Again.\n")
            self.login()

        elif confirmation == "Account Not Recognised":
            print("\n Your Account Was Not Found In Our Database.\n Try Creating One.\n")


    def send(self, message: str):
        bytes_all = message.encode(self.ENCODING)
        bytes_sent = self.socket.send(bytes_all)

        if bytes_all != bytes_sent:
            return False
        
        return True


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