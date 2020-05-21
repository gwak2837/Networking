# 20171758 Gwak Taeuk
# ChatTCPServer.py

from socket import *
from time import *
from threading import Thread
from threading import Lock
import json


# manage a client connection socket on a list, and count the number of live client socket
class ClinetSockets:
    def __init__(self):
        self.clientSocketCount = 0
        self.clientNicknameSocket = {}  # { clientNickname: [clientIP, clientPort, clientConnectionSocket], ... }
        self.lock = Lock()              # Lock for clientSocketCount
        self.lock2 = Lock()             # Lock for clientNicknameSocket

    def increaseCount(self):
        self.lock.acquire()
        self.clientSocketCount += 1
        self.lock.release()

    def decreaseCount(self):
        self.lock.acquire()
        self.clientSocketCount -= 1
        self.lock.release()

    def deleteNickname(self, nickname):
        self.lock2.acquire()
        del self.clientNicknameSocket[nickname]
        self.lock2.release()

    def addNickname(self, nickname, clientInfo):
        self.lock2.acquire()
        self.clientNicknameSocket[nickname] = clientInfo
        self.lock2.release()

# If N client connects, there will be N client threads, N client sockets, along with 1 serer socket in the main thread
# In this way, threading will automatically take care of multiple clients
def connectionThread(clientSockets, connectionSocket):
    clientInfo = json.loads(connectionSocket.recv(128).decode('utf-8'))
    nickname = clientInfo['nickname']
    if(clientSockets.clientSocketCount > MAX_USER_COUNT_IN_CHATROOM):
        connectionSocket.send(CHATROOM_FULL.encode('utf-8'))
        connectionSocket.close()
        return
    elif(not isValidNickname(nickname)):
        connectionSocket.send(INVALID_NICKNAME.encode('utf-8'))
        connectionSocket.close()
        return
    else:
        connectionSocket.send(CHATROOM_ENTRY_SUCCESS.encode('utf-8'))

    clientSockets.increaseCount()
    clientSockets.addNickname(nickname, [clientInfo['IP'], clientInfo['port'], connectionSocket])
    print(nickname, 'joined. There are', clientSockets.clientSocketCount, 'users connected.')

    # send chatroom infomation to the client
    chatroomInfo = {
        'serverIP': serverSocket.getsockname()[0],
        'serverPort': serverSocket.getsockname()[1],
        'userCount': clientSockets.clientSocketCount
    }
    response = json.dumps(chatroomInfo)
    connectionSocket.send(response.encode('utf-8'))

    while True:
        # server will receive the command and reply with an appropriate response based on the command
        request = connectionSocket.recv(1024).decode('utf-8')
        
        # when the connection disconnects for the TCP case, or when client disconnects
        if(request == ''):
            break
        
        # extract command number from client request
        request = json.loads(request)
        cmd = request['cmd']
        print('Command', cmd)

        # show the <nickname, IP, port> list of all users
        if(cmd == CLIENT_USERS):
            response = json.dumps(clientSockets.clientNicknameSocket)
            connectionSocket.send(response.encode('utf-8'))
        #
        elif(cmd == CLIENT_WHISPER):
            if(request['whisperTo'] not in clientSockets.clientNicknameSocket):
                connectionSocket.send(CLIENT_WHISPER_NO_USER.encode('utf-8'))
            else:
                connectionSocket.send(CLIENT_WHISPER_SUCCESS.encode('utf-8'))
                clientSockets.clientNicknameSocket[request['whisperTo']][2].send()

            response = json.dumps(clientSockets.clientNicknameSocket)
        # disconnect from server, and quit
        elif(cmd == CLIENT_EXIT):
            break
        # change client nickname
        elif(cmd == CLIENT_RENAME):
            newNickname = request['newNickname']
            if(isValidNickname(newNickname)):
                clientSockets.deleteNickname(nickname)
                clientSockets.addNickname(newNickname, [clientInfo['IP'], clientInfo['port'], connectionSocket])
                nickname = newNickname
                connectionSocket.send(VALID_NICKNAME.encode('utf-8'))
            else:
                connectionSocket.send(INVALID_NICKNAME.encode('utf-8'))
        # 
        elif(cmd == CLIENT_RTT):
            connectionSocket.send(CLIENT_RTT_REPLY.encode('utf-8'))        
        #
        elif(cmd == CLIENT_CHAT):
            response = request['msg']
        #          
        else:
            print('Unknown Response, Command', cmd)
            continue
            
    connectionSocket.close()
    clientSockets.deleteNickname(nickname)
    clientSockets.decreaseCount()

def closeAllClientSockets(clientSockets):
    for clientSocket in clientSockets.clientSockets:
        if(clientSocket != None):
            clientSocket.close()
        
    print('Number of times server have connected clients so far =', len(clientSocketCounter.clientSockets))

def isValidNickname(nickname):
    if(nickname in clientSockets.clientNicknameSocket or len(nickname) > 32):
        return False
    return True


# Command Encoding
CHATROOM_FULL = '00'
INVALID_NICKNAME = '01'
VALID_NICKNAME = '02'
CHATROOM_ENTRY_SUCCESS = '1'
CLIENT_USERS = '3'
CLIENT_WHISPER = '4'
CLIENT_WHISPER_NO_USER = '40'
CLIENT_WHISPER_SUCCESS = '41'
CLIENT_EXIT = '5'
CLIENT_VERSION = '6'
CLIENT_RENAME = '7'
CLIENT_RTT = '8'
CLIENT_RTT_REPLY = '80'
CLIENT_CHAT = '9'
MAX_USER_COUNT_IN_CHATROOM = 3

# create TCP socket that following IPv4 on the serverPort
# use own designated port number for the server socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverPort = 21758
serverSocket.bind(('', serverPort))

# print the port number of the server socket
print("The server socket was created on port", serverSocket.getsockname()[1])

# listen to server port
serverSocket.listen(1)
print("The server socket is listening to port", serverSocket.getsockname()[1])

# Give each client a unique number when they connect
clientSockets = ClinetSockets()

# try to accept, send, and receive
try:
    # Server has a main thread with a server socket that is waiting for client connections
    while True:
        # When a client connects to the server and server 'accept()'s, server has a new socket for that client
        (connectionSocket, clientAddress) = serverSocket.accept()
        # Server creates a new thread for client connection. The client socket is given to the client thread
        t2 = Thread(target=connectionThread, args=(clientSockets, connectionSocket))
        # Then, this client thread in the server will use the client socket to communicate with the client
        t2.daemon = True
        t2.start()

# when the user enters ‘Ctrl-C’, the program should not show any error messages
except KeyboardInterrupt:
    print('\nBye bye~')
# client shutdown without notice?
except (ConnectionResetError, BrokenPipeError):
    print('ConnectionResetError: Connection is reset by remote host')

closeAllClientSockets(clientSockets)
serverSocket.close()
