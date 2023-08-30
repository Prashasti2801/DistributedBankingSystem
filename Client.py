# To create user interface
# import tkinter 
# import PySimpleGUI
import socket



# Client class
class Client:
    def __init__(self, acc):
        self.account = acc      # Account number of client 
        self.clock = 0          # Client clock to send timestamps to server 
        self.waiting = False    # Variable to indicate request for resource 
        self.holding = False    # Variable to indicate usage of resource
        self.queue = []         # List to store the messages sent to server

    # Function to deposit amount
    def Deposit(self):
        acc = int(input("Enter Account: "))
        amt = float(input("Enter Amount: "))
        msg = 'Deposit,' + str(acc) + ',' + str(amt)
        return(msg)

    # Function to withdraw amount 
    def Withdraw(self):
        acc = int(input("Enter Account: "))
        amt = float(input("Enter Amount: "))
        msg = 'Withdraw,' + str(acc) + ',' + str(amt)
        return(msg)

    # Function to return amount
    def Query(self):
        acc = int(input("Enter Account: "))
        msg = 'Query,' + str(acc)
        return(msg)

    # Function to tranfer amount
    def Transfer(self):
        src_acc = int(input("Enter Source Account: "))
        dest_acc = int(input("Enter Destination Account: "))
        amt = float(input("Enter Amount: "))
        msg = 'Transfer,' + str(src_acc) + ',' + str(dest_acc) + ',' + str(amt)
        return(msg)
    
    # User function menu
    def user_input(self):
        option = input()
        match option:
            case "1":
                msg = self.Deposit() 
            case "2":
                msg = self.Withdraw()
            case "3":
                msg = self.Query()
            case "4":
                msg = self.Transfer()
            case "5": 
                msg = "Release"
            case default:
                msg = "Try Again"
        
        self.queue.append(msg)

        if msg == "Try Again":
            print("Enter option: ")
            self.user_input()

        return msg
    
    # Send Request message to the server
    def request(self):
        self.clock += 1                         # Increase the self clock to 1 at every request message 
        result = client_socket.recv(1024)
        print(f'Received data: {result.decode()}\n') 
        data = "Request:" + str(self.clock)
        client_socket.send(data.encode())       # Send data to the server for request access 
        
        result = client_socket.recv(1024).decode()

        # Server response to request message
        if result == 'Access granted':
            print('Access granted by the server\n')
            return True
        else:
            print('Access denied by the server\n')
            return False


# Main Execution Loop


client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # Create a socket object
host = '192.168.29.21'                                                  # Server's IP address
port = 12345                                                            # Server's port number

# Connect to server
try:
    client_socket.connect((host, port))
except socket.error as msg:
    print(f'Connection failed. Error code: {msg.errno}. Error message: {msg.strerror}')
    exit()



# User Interface 

client = Client(30124578451001)     # Create client object

val = client.request()              # Send request message to server
client.waiting = True
client.holding = False

if (val):
    client.waiting = False
    client.holding = True
    
    while True:                     # Communication Loop
        print("___________________________________________________________________________")
        print("Input option\n1: Deposit\n2: Withdrawl\n3: Query\n4: Transfer\n5: Exit\n\nEnter: ")      # Menu to call functions
        data = client.user_input()                                                                      # Get the message according to input from the user
        client_socket.send(data.encode())                                                               # Sending data to the server
        
        # Release message sent to server
        if data == "Release":
            client.waiting = False
            client.holding = False
            print("Client Closed")
            client_socket.close()
            exit()
        
        result = client_socket.recv(1024)
        print(f'Received data: {result.decode()}')
        print("___________________________________________________________________________")

else:
    print('Access not granted... Try again')
    client_socket.close()
    
