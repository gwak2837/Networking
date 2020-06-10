# 20171758 Gwak Taeuk
# FileChatTCPServer.py

from socket import *
from time import *
from threading import Thread
from threading import Lock
import pickle


# manage a client connection socket on a list, and count the number of live client socket
class ClinetSockets:
    def __init__(self):
        self.clientSocketCount = 0
        self.clientNicknameSocket = {}  # { clientNickname: [clientIP, clientPort, clientConnectionSocket], ... }
        self.lock = Lock()  # Lock for clientSocketCount
        self.lock2 = Lock()  # Lock for clientNicknameSocket

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
def connectionThread(clientSockets, connectionSocket, clientAddress):
    # list of banned(taboo) words
    tabooWords = ["i hate professor"]

    nickname = ""
    try:
        # check whether client nickname is valid and the number of users in chatroom exceed the maximum
        request = pickle.loads(connectionSocket.recv(1024))
        cmd = request["cmd"]
        response = {}
        if cmd == PRECONNECT:
            nickname = request["nickname"]
            if clientSockets.clientSocketCount >= MAX_USER_COUNT_IN_CHATROOM:
                response["cmd"] = PRECONNECT_CHATROOM_FULL
                connectionSocket.send(pickle.dumps(response, protocol=4))
                connectionSocket.close()
                return
            elif not isValidNickname(nickname):
                response["cmd"] = PRECONNECT_INVALID_NICKNAME
                connectionSocket.send(pickle.dumps(response, protocol=4))
                connectionSocket.close()
                return
            else:
                clientSockets.increaseCount()
                clientSockets.addNickname(nickname, (clientAddress[0], clientAddress[1], connectionSocket))
                response["cmd"] = PRECONNECT_SUCCESS
                response["serverIP"] = serverSocket.getsockname()[0]
                response["serverPort"] = serverSocket.getsockname()[1]
                response["userCount"] = clientSockets.clientSocketCount
                connectionSocket.send(pickle.dumps(response, protocol=4))
                print(nickname, "joined. There are", clientSockets.clientSocketCount, "users connected.")
        else:
            print("Invalid Request, Command", cmd)
            connectionSocket.close()
            return

        # handle requests from the clients
        while True:
            # server will receive the command and reply with an appropriate response based on the command
            requestBytes = connectionSocket.recv(2048)

            # when the connection disconnects for the TCP case, or when client disconnects
            if requestBytes == "":
                break

            # extract command number from client request
            requestBuffer = [requestBytes]
            while True:
                try:
                    request = pickle.loads(requestBytes)
                    break
                except pickle.UnpicklingError:
                    requestBuffer.append(connectionSocket.recv(2048))
                    requestBytes = b"".join(requestBuffer)
                    continue

            cmd = request["cmd"]
            print("Command", cmd)
            response = {}

            # show the <nickname, IP, port> list of all users
            if cmd == USERS:
                response["cmd"] = USERS_RESPONSE
                users = []

                for clientNickname in clientSockets.clientNicknameSocket:
                    users.append(
                        [
                            clientNickname,
                            clientSockets.clientNicknameSocket[clientNickname][0],
                            clientSockets.clientNicknameSocket[clientNickname][1],
                        ]
                    )

                response["users"] = users
                connectionSocket.send(pickle.dumps(response, protocol=4))
            # whisper to specified user
            elif cmd == WHISPER:
                whisperTo = request["whisperTo"]
                message = request["msg"]
                # if there is no user whisper to
                if whisperTo not in clientSockets.clientNicknameSocket:
                    response["cmd"] = WHISPER_NO_USER
                    connectionSocket.send(pickle.dumps(response, protocol=4))
                ############# to do
                elif not isValidMessage(message, tabooWords):
                    break
                elif whisperTo == nickname:
                    response["cmd"] = WHISPER_MYSELF
                    connectionSocket.send(pickle.dumps(response, protocol=4))
                else:
                    response["cmd"] = WHISPER_SUCCESS
                    connectionSocket.send(pickle.dumps(response, protocol=4))
                    response2 = {}
                    response2["cmd"] = CHAT_RESPONSE
                    response2["from"] = nickname
                    response2["msg"] = message
                    clientSockets.clientNicknameSocket[whisperTo][2].send(pickle.dumps(response2, protocol=4))
            # disconnect from server, and quit
            elif cmd == EXIT:
                break
            # show server's software version (and client software version)
            elif cmd == VERSION:
                response["cmd"] = VERSION_RESPONSE
                response["version"] = SERVER_VERSION
                connectionSocket.send(pickle.dumps(response, protocol=4))
            # change client nickname
            elif cmd == RENAME:
                newNickname = request["newNickname"]
                if isValidNickname(newNickname):
                    clientSockets.deleteNickname(nickname)
                    clientSockets.addNickname(newNickname, (clientAddress[0], clientAddress[1], connectionSocket))
                    nickname = newNickname
                    response["cmd"] = RENAME_SUCCESS
                    response["nickname"] = nickname
                    connectionSocket.send(pickle.dumps(response, protocol=4))
                else:
                    response["cmd"] = RENAME_INVALID_NICKNAME
                    connectionSocket.send(pickle.dumps(response, protocol=4))
            # show RTT(Round Trip Time) from the client to the server and back
            elif cmd == RTT:
                response["cmd"] = RTT_RESPONSE
                response["startTime"] = request["startTime"]
                connectionSocket.send(pickle.dumps(response, protocol=4))
            # when a client send chat to the server, the chat should be delivered to everyone connected
            elif cmd == CHAT:
                message = request["msg"]
                if not isValidMessage(message, tabooWords):
                    break
                response["cmd"] = CHAT_RESPONSE
                response["from"] = nickname
                response["msg"] = message
                byteStream = pickle.dumps(response, protocol=4)
                for clientInfo in clientSockets.clientNicknameSocket.values():
                    # except the client who send the chat
                    if clientInfo[2] != connectionSocket:
                        clientInfo[2].send(byteStream)
            # send a file <filename> to all connected clients
            elif cmd == FILE_TRANSFER_ALL:
                response["cmd"] = FILE_TRANSFER_RESPONSE
                response["sender"] = request["sender"]
                response["fileHash"] = request["fileHash"]
                response["fileName"] = request["fileName"]
                response["fileBinaryData"] = request["fileBinaryData"]
                byteStream = pickle.dumps(response, protocol=4)

                # all other connected clients should receive this file, excluding the sender
                for clientInfo in clientSockets.clientNicknameSocket.values():
                    if clientInfo[2] != connectionSocket:
                        clientInfo[2].send(byteStream)

            elif cmd == FILE_TRANSFER_WHISPER:
                whisperTo = request["whisperTo"]
                # if there is no user whisper to
                if whisperTo not in clientSockets.clientNicknameSocket:
                    response["cmd"] = FILE_TRANSFER_WHISPER_NO_USER
                    connectionSocket.send(pickle.dumps(response, protocol=4))
                # if whisper myself
                elif whisperTo == nickname:
                    response["cmd"] = FILE_TRANSFER_WHISPER_MYSELF
                    connectionSocket.send(pickle.dumps(response, protocol=4))
                # if suceed
                else:
                    response["cmd"] = FILE_TRANSFER_RESPONSE
                    response["sender"] = request["sender"]
                    response["fileHash"] = request["fileHash"]
                    response["fileName"] = request["fileName"]
                    response["whisperTo"] = whisperTo
                    response["fileBinaryData"] = request["fileBinaryData"]
                    clientSockets.clientNicknameSocket[whisperTo][2].send(pickle.dumps(response, protocol=4))
            # Invalid client request
            else:
                print("Invalid Request, Command", cmd)
                continue

    except ConnectionResetError:
        print("ConnectionResetError: Connection is reset by remote host")
    except BrokenPipeError:
        print("BrokenPipeError: Connection disconnected while processing recv() or send()")

    connectionSocket.close()
    clientSockets.deleteNickname(nickname)
    clientSockets.decreaseCount()

    response = {}
    response["cmd"] = EXIT_RESPONSE
    response["nickname"] = nickname
    response["userCount"] = clientSockets.clientSocketCount
    byteStream = pickle.dumps(response, protocol=4)
    for clientNickname in clientSockets.clientNicknameSocket:
        clientSockets.clientNicknameSocket[clientNickname][2].send(byteStream)


def closeAllConnectionSockets(clientSockets):
    for clientNickname in clientSockets.clientNicknameSocket:
        clientSockets.clientNicknameSocket[clientNickname][2].close()
    print(len(clientSockets.clientNicknameSocket), "clients are connecting when server shuts down")


def isValidNickname(nickname):
    if nickname in clientSockets.clientNicknameSocket or len(nickname) > 32:
        return False
    return True


def isValidMessage(message, tabooWords):
    for tabooWord in tabooWords:
        if message.lower().find(tabooWord) >= 0:
            return False
    return True


# Command Encoding
PRECONNECT = "0"
PRECONNECT_CHATROOM_FULL = "00"
PRECONNECT_INVALID_NICKNAME = "01"
PRECONNECT_SUCCESS = "02"
USERS = "1"
USERS_RESPONSE = "10"
WHISPER = "2"
WHISPER_NO_USER = "20"
WHISPER_MYSELF = "21"
WHISPER_SUCCESS = "22"
EXIT = "3"
EXIT_RESPONSE = "30"
VERSION = "4"
VERSION_RESPONSE = "40"
RENAME = "5"
RENAME_INVALID_NICKNAME = "50"
RENAME_SUCCESS = "51"
RTT = "6"
RTT_RESPONSE = "60"
CHAT = "7"
CHAT_RESPONSE = "70"
FILE_TRANSFER_ALL = "8"
FILE_TRANSFER_WHISPER = "9"
FILE_TRANSFER_WHISPER_NO_USER = "90"
FILE_TRANSFER_WHISPER_MYSELF = "91"
FILE_TRANSFER_RESPONSE = "92"
MAX_USER_COUNT_IN_CHATROOM = 10
SERVER_VERSION = "1.0"
CLIENT_VERSION = "1.0"

# create TCP socket that following IPv4 on the serverPort
# use own designated port number for the server socket
serverSocket = socket(AF_INET, SOCK_STREAM)
serverName = "localhost"
serverPort = 21758
serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind((serverName, serverPort))

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
        t = Thread(target=connectionThread, args=(clientSockets, connectionSocket, clientAddress))
        # Then, this client thread in the server will use the client socket to communicate with the client
        t.daemon = True
        t.start()

# when the user enters ‘Ctrl-C’, the program should not show any error messages
except KeyboardInterrupt:
    pass

closeAllConnectionSockets(clientSockets)
serverSocket.close()
print("\nBye bye~")
