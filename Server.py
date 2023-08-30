import socket
import threading
from pymongo import MongoClient

# Connect to database cluster in MongoDB
cluster = MongoClient("mongodb+srv://dsproject:dsproject@cluster0.vuipzhy.mongodb.net/?retryWrites=true&w=majority")
db = cluster.bank_accounts


# Bank server class
class BankServer:
    def __init__(self):
        self.request_queue = []         # Queue to store incoming requests
        self.granted_queue = []         # Queue to store processed request, acts as history
        self.clients = []               # Clients connected to server, maximum 5 at a time
        self.clientaccess = -1          # Current client
        self.clock = 0                  # Server clock

    # Load the customer document from MongoDB cluster
    def load(self, acnt):
        accounts = db.customer_info
        customer = accounts.find_one({"Account_no": acnt})
        if customer:
            return customer
        else:
            return None
        
    # Function to deposit amount in a account
    def Deposit(self, acnt, amt):
        # Load the customer document with the given account number
        customer = db.customer_info.find_one({"Account_no": acnt})

        if customer:
            # Get the current balance from the customer document
            current_balance = customer["Balance"]

            # Calculate the new balance after the deposit
            new_balance = current_balance + amt

            # Update the balance field in the document
            db.customer_info.update_one({"Account_no": acnt}, {
                                        "$set": {"Balance": new_balance}})

            # Return a success message
            return (f"Deposit of {amt} was successful. New balance: {new_balance}")
        
        else:
            # Return an error message if the account number is not found
            return ("Account not found!")

    def Withdraw(self, acnt, amt):
        # Load the customer document with the given account number
        customer = db.customer_info.find_one({"Account_no": acnt})

        if customer:
            # Get the current balance from the customer document
            current_balance = customer["Balance"]

            # Minimum Balance in the account to remain 2000
            if (current_balance - amt < 2000):
                return "Insufficient Balance!"

            # Calculate the new balance after the withdrawal
            new_balance = current_balance - amt

            # Update the balance field in the document
            db.customer_info.update_one({"Account_no": acnt}, {
                                        "$set": {"Balance": new_balance}})

            # Return a success message
            return f"Withdrawal of {amt} successfully. New balance: {new_balance}"
       
        else:
            # Return an error message if the account number is not found
            return "Account not found!"

    def Query(self, acnt):
        # Load the customer document with the given account number
        customer = db.customer_info.find_one({"Account_no": acnt})

        if customer:
            # Get the current balance from the customer document
            current_balance = customer["Balance"]

            # Return a success message
            return f"Current Balance: {current_balance}"
        
        else:
            # Return an error message if the account number is not found
            return "Account not found!"

    def Transfer(self, src_acnt, dest_acnt, amt):
        # Load the customer document with the given account number
        src_customer = db.customer_info.find_one({"Account_no": src_acnt})
        dest_customer = db.customer_info.find_one({"Account_no": dest_acnt})

        if (src_customer and dest_customer):
            # Get the current balance from the customer document
            src_balance = src_customer["Balance"]
            dest_balance = dest_customer["Balance"]

            # Minimum Balance in the source account to remain 2000
            if (src_balance - amt < 2000):
                return "Insufficient Balance!"
            
            src_balance = src_balance - amt
            dest_balance = dest_balance + amt

            db.customer_info.update_one({"Account_no": src_acnt}, {
                                        "$set": {"Balance": src_balance}})
            db.customer_info.update_one({"Account_no": dest_acnt}, {
                                        "$set": {"Balance": dest_balance}})

            # Return a success message
            return f"Transfer of {amt} successfully\nNew balance of Source account {src_acnt}: {src_balance}\nNew balance of Destination account {dest_acnt}: {dest_balance}"
        
        else:
            # Return an error message if the account number is not found
            return "Account not found!"

    # function to handle incoming client connections
    def handle_client(self, client_socket, client_address, client_id):      # Parametes are Client socket, address and index in the client list 
        # Feedback messages
        print(f"Client connected: {client_address}")
        client_socket.send(("Server connected successfully").encode())
        data = client_socket.recv(1024).decode()

        # Process the request message from the client
        req = data.split(':')[0]
        if req == 'Request':
            timestamp = int(data.split(':')[1])
            self.clock = max(self.clock, timestamp) + 1             # Update the local clock according to incoming requests
            self.request_queue.append((timestamp, client_id))       # Add every request for access to the request queue of server                    
            
            # Wait till the server grants access to the client
            while self.request_queue[0][1] != client_id or self.clientaccess != -1:
                pass                                                # Wait for access until the client reaches the fron of queue or there is no processing request presently
            
            # Access granted to the client
            self.granted_queue.append(self.request_queue[0])        # Add the client to the granted queue 
            self.request_queue.pop(0)                               # Remove from the request queue
            self.clientaccess = client_id                           # Update the present client
            client_socket.send('Access granted'.encode())
     
        else:
            client_socket.send(("Access not granted... Try again").encode())
            client_socket.close()


        # Loop to communicate with the client to process functions
        while True:
            # Receive data from the client
            rawdata = client_socket.recv(1024)
            data = rawdata.decode()
            print(f'Received data from {client_address}: {data}')

            # Works as a release message from client
            if (data == "Release"):
                self.clientaccess = -1          # Update the present working client as none
                return                          # Close the thread
            
            # Process the request
            funclist = data.split(',')
            acnt = (funclist[1])
            queryfunc = funclist[0]
            customer = self.load(acnt)
            message = ""

            # Invoke function to process request when customer exists
            if customer is not None:
                if queryfunc == "Deposit":
                    amt = float(funclist[2])
                    message = self.Deposit(acnt, amt)
                elif queryfunc == "Withdraw":
                    amt = float(funclist[2])
                    message = self.Withdraw(acnt, amt)
                elif queryfunc == "Query":
                    message = self.Query(acnt)
                elif queryfunc == "Transfer":
                    src_acnt = funclist[1]
                    dest_acnt = funclist[2]
                    amt = float(funclist[3])
                    message = self.Transfer(src_acnt, dest_acnt, amt)
            else:
                message = "Account not found!"

            # Send data back to the client
            client_socket.send(message.encode())
        
            
# Main Execution Loop

# Socket 
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)   # Create socket object
host = socket.gethostname()                                         # Local machine name
port = 12345                                                        # Port number

# Bind the socket to a public host and port
try:
    server_socket.bind((host, port))
except socket.error as msg:
    print(f'Bind failed. Error code: {msg.errno}. Error message: {msg.strerror}')
    exit()

# Become a server socket
try:
    server_socket.listen(5)         # Listen to 5 devices at a time
except socket.error as msg:
    print(f'Listen failed. Error code: {msg.errno}. Error message: {msg.strerror}')
    exit()



# Object of the Bankserver class
bank = BankServer()

# Accept incoming connections from clients and create a new thread to handle communication with each client
while True:
    try:
        client_socket, client_address = server_socket.accept()
        thread = threading.Thread(target=bank.handle_client, args=(client_socket, client_address, len(bank.clients)))
        bank.clients.append(thread)
        thread.start()

    except socket.error as msg:
        print(f'Socket error. Error code: {msg.errno}. Error message: {msg.strerror}')
        server_socket.close()       # Close the server socket and exit in case of error
        exit()
