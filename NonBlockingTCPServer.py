# 20171758 Gwak Taeuk
# BasicTCPServer.py

from socket import *
from time import *
from select import *
import json


# manage a client connection socket on a list, and count the number of live client socket
class ClinetSocketCounter:
    def __init__(self):
        self.clientserverSockets = []
        self.liveClientSocketCount = 0

# If N client connects, there will be N client threads, N client serverSockets, along with 1 serer socket in the main thread
# In this way, threading will automatically take care of multiple clients
def connection(connectionSocket, serverSockets, socketIDMap):
    # server will receive the command and reply with an appropriate response based on the command
    request = connectionSocket.recv(1024).decode()

    # when the connection disconnects for the TCP case, or when client disconnects
    if(request == ''):
        # Whenever an existing client disconnects, print out the client number and the number of clients as below
        connectionSocket.close()
        serverSockets.remove(connectionSocket)
        print('Client', socketIDMap[connectionSocket], 'disconnected. Number of connected clients =', len(serverSockets) - 1)
        del socketIDMap[connectionSocket]
        return

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
    else:
        print('Unknown Response, Command', command)

def closeAllSockets(sockets):
    for socket in sockets:
        socket.close()
        

# measure the server starting time
start = time()

# create TCP socket that following IPv4 on the serverPort
# use own designated port number for the server socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverPort = 21758
serverSocket.bind(('', serverPort))

# The server also maintains an array of client sockets that are connected
serverSockets = [serverSocket]

# print the port number of the server socket
print("The server socket was created on port", serverSocket.getsockname()[1])

# listen to server port
serverSocket.listen(1)
print("The server socket is listening to port", serverSocket.getsockname()[1])

# Give each client a unique number when they connect
clientID = 0
socketIDMap = {}

clientCounterTimer = time()

# try to accept, send, and receive
# No multi-threading, Server has only one thread with a server socket that is waiting for client connections
try:
    # Server has a main thread with a server socket that is waiting for client connections
    while True:
        # Server uses the 'select()' function to wait for all sockets simultaneously
        # All sockets mean, all clients sockets + the server socket. If N clients, N + 1 sockets
        readSockets, writeSockets, errorSockets = select(serverSockets, [], [], 1)
        
        if (time() - clientCounterTimer > 60):
            clientCounterTimer = time()
            print('Number of connected clients =', len(serverSockets) - 1)

        for readSocket in readSockets:
            if (readSocket == serverSocket):
                # When a client connects to the server and server 'accept()'s, server has a new socket for that client
                (connectionSocket, clientAddress) = serverSocket.accept()
                print('Connection requested from', clientAddress)

                # If a new client connection comes in, server will put that client socket into this array
                serverSockets.append(connectionSocket)
                socketIDMap[connectionSocket] = clientID            
                
                # Whenever a new client connects, print out the client number and the number of clients as below
                print('Client', clientID, 'connected.    Number of connected clients =', len(serverSockets) - 1)

                # Client ID should not change even if a client disconnect. 
                # Client ID increases by 1 every time connecting with a client
                clientID += 1

            else:
                connection(readSocket, serverSockets, socketIDMap)
        
        if (len(errorSockets) > 0):
            print('Error socket list:')
            for errorSocket in errorSockets:
                print('Client socket #', socketIDMap[errorSocket])
            

# when the user enters ‘Ctrl-C’, the program should not show any error messages
except KeyboardInterrupt:
    print('\nBye bye~')
# client shutdown without notice?
except ConnectionResetError:
    print('ConnectionResetError: Connection is reset by remote host')

closeAllSockets(serverSockets)
serverSocket.close()
