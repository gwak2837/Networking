# 20171758 Gwak Taeuk
# BasicTCPServer.py

from socket import *
from time import *
from threading import Thread
import json


# manage a client connection socket on a list, and count the number of live client socket
class ClinetSocketCounter:
    def __init__(self):
        self.clientSockets = []
        self.liveClientSocketCount = 0

# If N client connects, there will be N client threads, N client sockets, along with 1 serer socket in the main thread
# In this way, threading will automatically take care of multiple clients
def connectionThread(clientSocketCounter, clientID):
    # send and receive data through the connection socket
    while True:
        # get client socket(connection socket) by client ID
        connectionSocket = clientSocketCounter.clientSockets[clientID]
        # server will receive the command and reply with an appropriate response based on the command
        request = connectionSocket.recv(1024).decode()
        # when the connection disconnects for the TCP case, or when client disconnects
        if(request == ''):
            break
        # extract command number from client request
        requestJson = json.loads(request)
        command = requestJson['command']

        # convert text to UPPER-case letters
        if(command == '1'):
            print('Command', command)
            response = requestJson['message'].upper()
            connectionSocket.send(response.encode())
        # tell the client what the IP address and port number of the client is
        elif(command == '2'):
            print('Command', command)
            address = {
                "IP": clientAddress[0],
                "Port": clientAddress[1]
            }
            response = json.dumps(address)
            connectionSocket.send(response.encode())
        # tell the client what the current time on the server is
        elif(command == '3'):
            print('Command', command)
            connectionSocket.send(strftime(
                '%H-%M-%S', localtime(time())).encode())  # TCP
        # tell the client how long it (server program) has been running for
        elif(command == '4'):
            print('Command', command)
            connectionSocket.send(strftime(
                '%H-%M-%S', gmtime(time() - start)).encode())  # TCP
        # test time out
        elif(command == '6'):
            print('Command', command)
            sleep(15)
        # test buffer overflow
        elif(command == '7'):
            print('Command', command)
            response = requestJson['message']
            connectionSocket.send(response.encode())
        else:
            print('Unknown Response, Command', command)
            continue

    connectionSocket.close()
    connectionSocket = None
    clientSocketCounter.liveClientSocketCount -= 1

    # Whenever an existing client disconnects, print out the client number and the number of clients as below
    print('Client', clientID, 'disconnected. Number of connected clients =', clientSocketCounter.liveClientSocketCount)

# The server must print out the number of client every 1 minute by a thread
def counterThread(clientSocketCounter):
    while True:
        print('Number of connected clients =', clientSocketCounter.liveClientSocketCount)
        sleep(60)

def closeAllClientSockets(clientSocketCounter):
    for clientSocket in clientSocketCounter.clientSockets:
        if(clientSocket != None):
            clientSocket.close()
        
    print('Number of times server have connected clients so far =', len(clientSocketCounter.clientSockets))

# measure the server starting time
start = time()

# create TCP socket that following IPv4 on the serverPort
# use own designated port number for the server socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverPort = 21758
serverSocket.bind(('', serverPort))
clientSocketCounter = ClinetSocketCounter()

# print the port number of the server socket
print("The server socket was created on port", serverSocket.getsockname()[1])

# listen to server port
serverSocket.listen(1)
print("The server socket is listening to port", serverSocket.getsockname()[1])

# Give each client a unique number when they connect
clientID = 0
t = Thread(target=counterThread, args=(clientSocketCounter,))
t.daemon = True
t.start()

# try to accept, send, and receive
try:
    # Server has a main thread with a server socket that is waiting for client connections
    while True:
        # When a client connects to the server and server 'accept()'s, server has a new socket for that client
        (connectionSocket, clientAddress) = serverSocket.accept()     
        print('Connection requested from', clientAddress)        

        clientSocketCounter.clientSockets.append(connectionSocket) 
        clientSocketCounter.liveClientSocketCount += 1

        # Whenever a new client connects, print out the client number and the number of clients as below
        print('Client', clientID, 'connected.    Number of connected clients =', clientSocketCounter.liveClientSocketCount)

        # Server creates a new thread for client connection. The client socket is given to the client thread
        t2 = Thread(target=connectionThread, args=(clientSocketCounter, clientID))
        # Then, this client thread in the server will use the client socket to communicate with the client
        t2.daemon = True
        t2.start()

        # Client ID should not change even if a client disconnect. 
        # Client ID increases by 1 every time connecting with a client
        clientID += 1

# when the user enters ‘Ctrl-C’, the program should not show any error messages
except KeyboardInterrupt:
    print('\nBye bye~')
# client shutdown without notice?
except ConnectionResetError:
    print('ConnectionResetError: Connection is reset by remote host')

closeAllClientSockets(clientSocketCounter)
serverSocket.close()
