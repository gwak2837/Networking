# 20170825 Seo Shinak
# ChatTCPServer.py

import socket
import threading
import json

# class for sharing data for connection thread
class ClientsInfo:
    def __init__(self):
        self.clientsInfo = {}  # { nickname: [IP, port, connectionSocket], ... }
        self.lock = threading.Lock()  # lock for dictionary of clientsInfo

    def addClientInfo(self, nickname, IP, port, connectionSocket):
        self.lock.acquire()
        self.clientsInfo[nickname] = [IP, port, connectionSocket]
        self.lock.release()

    def deleteClientInfo(self, nickname):
        self.lock.acquire()
        del self.clientsInfo[nickname]
        self.lock.release()


# check whether message has banned words
def isValidMessage(message, bannedWords):
    for bannedWord in bannedWords:
        if message.lower().find(bannedWord) >= 0:
            return False
    return True


# function for a connection thread
def connection(clientsInfo, connectionSocket, clientAddress):
    nickname = ""
    bannedWords = ["i hate professor"]
    try:
        request = json.loads(connectionSocket.recv(1024).decode("utf-8"))
        cmd = request["cmd"]
        response = {}

        # receive a request from the client. there are 1 kinds of request.
        # - CONNECT : a client want to connect to the server. (want to enter to a chatroom)
        if cmd == CONNECT:
            nickname = request["nickname"]

            # send a response to the client. there are 3 kinds of response.
            # - CONNECT_DUPLICATE_NICKNAME : The nickname is already used by someone else.
            # - CONNECT_CHATROOM_FULL : The chatroom is full.
            # - CONNECT_SUCCESS : The client has successfully connected to the server
            if nickname in clientsInfo.clientsInfo:
                response["cmd"] = CONNECT_DUPLICATE_NICKNAME
                connectionSocket.send(json.dumps(response).encode("utf-8"))
                connectionSocket.close()
                return
            elif len(clientsInfo.clientsInfo) == MAX_USER_IN_CHATROOM:
                response["cmd"] = CONNECT_CHATROOM_FULL
                connectionSocket.send(json.dumps(response).encode("utf-8"))
                connectionSocket.close()
                return
            else:
                userCount = len(clientsInfo.clientsInfo) + 1
                responseToEveryone = {}
                responseToEveryone["cmd"] = NEW_USER_ENTERS
                responseToEveryone["nickname"] = nickname
                responseToEveryone["userCount"] = userCount
                responseToEveryoneByte = json.dumps(responseToEveryone).encode("utf-8")
                for clientInfo in clientsInfo.clientsInfo.values():
                    clientInfo[2].send(responseToEveryoneByte)

                clientsInfo.addClientInfo(nickname, clientAddress[0], clientAddress[1], connectionSocket)
                response["cmd"] = CONNECT_SUCCESS
                response["serverAddress"] = serverSocket.getsockname()
                response["userCount"] = userCount
                print(nickname, "joined. There are", userCount, "users connected.")
                connectionSocket.send(json.dumps(response).encode("utf-8"))
        else:
            print("Invalid request command. Command:", cmd)
            connectionSocket.close()
            return

        while True:
            # receive a request from the client. there are 7 kinds of requests.
            # - USERS : show the <nickname, IP, port> list of all users
            # - WHISPER : whisper to <nickname>
            # - EXIT : disconnect from server, and quit client process
            # - VERSION : show server's software version (and client software version)
            # - RENAME : change client nickname
            # - RTT : show RTT(Round Trip Time) from the client to the server and back
            # - CHAT : send a chat to all users in the chatroom
            requestString = connectionSocket.recv(1024).decode("utf-8")

            # if the client disconnects server, or connection to the client has been lost
            if requestString == "":
                print("The TCP connection to the clinet(nickname=" + nickname + ") has been lost.")
                break

            request = json.loads(requestString)
            cmd = request["cmd"]
            print("Command", cmd)
            response = {}

            # send a response to the client. there are 1 kinds of response.
            # - USERS_RESPONSE : send the <nickname, IP, port> list of all users
            if cmd == USERS:
                users = []  # [[clientNickname, clientIP, clientPort], ...]
                for clientNickname, clientInfo in clientsInfo.clientsInfo.items():
                    users.append([clientNickname, clientInfo[0], clientInfo[1]])
                response["cmd"] = USERS_RESPONSE
                response["users"] = users
                connectionSocket.send(json.dumps(response).encode("utf-8"))
            # send a response to the client. there are 3 kinds of response.
            # - WHISPER_NO_SUCH_USER : there is no user 'whispering to'
            # - WHISPER_MYSELF : cannot whisper myself
            # - WHISPER_SUCCESS : succeed to whisper
            elif cmd == WHISPER:
                to = request["to"]
                msg = request["msg"]
                if to not in clientsInfo.clientsInfo:
                    response["cmd"] = WHISPER_NO_SUCH_USER
                elif clientsInfo.clientsInfo[to][2] == connectionSocket:
                    response["cmd"] = WHISPER_MYSELF
                elif not isValidMessage(msg, bannedWords):
                    break
                else:
                    responseToReceiver = {}
                    responseToReceiver["cmd"] = CHAT_RESPONSE
                    responseToReceiver["from"] = nickname
                    responseToReceiver["msg"] = msg
                    clientsInfo.clientsInfo[to][2].send(json.dumps(responseToReceiver).encode("utf-8"))
                    response["cmd"] = WHISPER_SUCCESS
                connectionSocket.send(json.dumps(response).encode("utf-8"))
            # send a response to the client. there are 3 kinds of response.
            # - EXIT_BROADCAST : broadcast the fact that a user left the chatroom to all users
            elif cmd == EXIT:
                break
            # send a response to the client. there are 3 kinds of response.
            # - VERSION_RESPONSE : send server version to the client
            elif cmd == VERSION:
                response["cmd"] = VERSION_RESPONSE
                response["serverVersion"] = SERVER_VERSION
                connectionSocket.send(json.dumps(response).encode("utf-8"))
            # send a response to the client. there are 3 kinds of response.
            # - RENAME_DUPLICATE_NICKNAME : cannot change to the <nickname> because the <nickname> is userd by another user
            # - RENAME_SUCCESS : change client nickname
            elif cmd == RENAME:
                newNickname = request["newNickname"]
                if newNickname in clientsInfo.clientsInfo:
                    response["cmd"] = RENAME_DUPLICATE_NICKNAME
                else:
                    clientsInfo.deleteClientInfo(nickname)
                    clientsInfo.addClientInfo(newNickname, clientAddress[0], clientAddress[1], connectionSocket)
                    nickname = newNickname
                    response["cmd"] = RENAME_SUCCESS
                    response["newNickname"] = newNickname
                connectionSocket.send(json.dumps(response).encode("utf-8"))
            # send a response to the client. there are 3 kinds of response.
            # - RTT_RESPONSE : send back a 'beginTime' to the client as it is
            elif cmd == RTT:
                response["cmd"] = RTT_RESPONSE
                response["beginTime"] = request["beginTime"]
                connectionSocket.send(json.dumps(response).encode("utf-8"))
            # send a response to the client. there are 3 kinds of response.
            # - CHAT_RESPONSE : send back a 'msg' to all users in the chatroom as it is
            # - EXIT_BROADCAST : disconnects the client if message from the client has banned words
            elif cmd == CHAT:
                msg = request["msg"]
                if not isValidMessage(msg, bannedWords):
                    break
                else:
                    response["cmd"] = CHAT_RESPONSE
                    response["from"] = nickname
                    response["msg"] = msg
                    responseByte = json.dumps(response).encode("utf-8")
                    for clientInfo in clientsInfo.clientsInfo.values():
                        if clientInfo[2] != connectionSocket:
                            clientInfo[2].send(responseByte)
            # Undefined request comnmand
            else:
                print("Invalid request command. Command:", cmd)
    except Exception as e:
        print(e)

    # disconnect the client and broadcast the fact that a user left the chatroom to all users
    connectionSocket.close()
    clientsInfo.deleteClientInfo(nickname)
    response = {}
    response["cmd"] = EXIT_BROADCAST
    response["nickname"] = nickname
    response["userCount"] = len(clientsInfo.clientsInfo)
    responseByte = json.dumps(response).encode("utf-8")
    for clientInfo in clientsInfo.clientsInfo.values():
        clientInfo[2].send(responseByte)


# command list
MAX_USER_IN_CHATROOM = 10
SERVER_VERSION = "1"
CLIENT_VERSION = "1"
CONNECT = "0"
CONNECT_DUPLICATE_NICKNAME = "01"
CONNECT_CHATROOM_FULL = "02"
CONNECT_SUCCESS = "03"
USERS = "1"
USERS_RESPONSE = "10"
WHISPER = "2"
WHISPER_NO_SUCH_USER = "20"
WHISPER_MYSELF = "21"
WHISPER_SUCCESS = "22"
EXIT = "3"
EXIT_BROADCAST = "30"
VERSION = "4"
VERSION_RESPONSE = "40"
RENAME = "5"
RENAME_DUPLICATE_NICKNAME = "50"
RENAME_SUCCESS = "51"
RTT = "6"
RTT_RESPONSE = "60"
CHAT = "7"
CHAT_RESPONSE = "70"
NEW_USER_ENTERS = "8"

# server state
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverName = "nsl2.cau.ac.kr"
serverPort = 20825
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSocket.bind((serverName, serverPort))
serverSocket.listen(1)
print("The server socket is listening on", serverSocket.getsockname())

# list of imformation of clients
clientsInfo = ClientsInfo()

# main thread of server waits for the connection of clients
try:
    while True:
        # create a new thread when the server and client are connected
        # when the main thread is terminated, this thread is also automatically terminated
        (connectionSocket, clientAddress) = serverSocket.accept()
        connectionThread = threading.Thread(target=connection, args=(clientsInfo, connectionSocket, clientAddress))
        connectionThread.daemon = True
        connectionThread.start()
# when Ctrl+C pressed in the server's main thread
except KeyboardInterrupt:
    pass

# close all connection sockets and the server socket
for clientInfo in clientsInfo.clientsInfo.values():
    clientInfo[2].close()
serverSocket.close()

print("\nBye bye~")
