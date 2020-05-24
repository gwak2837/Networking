# 20170825 Seo Shinak
# ChatTCPServer.py

import socket
import threading
import json
import sys
import time


# for sharing the client socket between threads
class ClientSocket:
    def __init__(self, clientSocket, nickname):
        self.clientSocket = clientSocket
        self.nickname = nickname


# return clientSocket if a client have successfully connected to the server,
# return None if if a client failed to connect to the server.
def connectServer(serverName, serverPort, clientPort, nickname):
    # create client socket and set timeout of 5 secs
    clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientSocket.settimeout(5)

    # try to connect to the server up to 10 times
    connectionSuccess = False
    for _ in range(10):
        try:
            # connect to the server
            clientSocket.connect((serverName, serverPort))

            # send client nickname to the server
            request = {}
            request["cmd"] = CONNECT
            request["nickname"] = nickname
            clientSocket.send(json.dumps(request).encode("utf-8"))

            # receive a response from the server. there are 3 kinds of responses.
            # - CONNECT_DUPLICATE_NICKNAME : The nickname is already used by someone else.
            # - CONNECT_CHATROOM_FULL : The chatroom is full.
            # - CONNECT_SUCCESS : The client has successfully connected to the server
            response = json.loads(clientSocket.recv(1024).decode("utf-8"))
            cmd = response["cmd"]
            if cmd == CONNECT_DUPLICATE_NICKNAME:
                print("The nickname is already used by someone else. Use another nickname.")
            elif cmd == CONNECT_CHATROOM_FULL:
                print("The chatroom is full. Please try again later.")
            elif cmd == CONNECT_SUCCESS:
                print(
                    "Welcome",
                    nickname,
                    "to cau-netclass chatroom at",
                    response["serverAddress"][0],
                    response["serverAddress"][1],
                )
                print("You are", response["userCount"], "th user.")
                connectionSuccess = True
            else:
                print("Invalid response command. Command:", cmd)

            break
        except Exception as e:
            print(e)
            time.sleep(1)

    # if a client failed to connect to the server
    if connectionSuccess == False:
        clientSocket.close()
        return None

    # return clientSocket if a client have successfully connected to the server
    return clientSocket


# function for receiving thread
def receive(iClientSocket):
    clientSocket = iClientSocket.clientSocket
    while True:
        try:
            responseString = clientSocket.recv(1024).decode("utf-8")
        except socket.timeout:
            continue

        # if the server disconnects client, or connection to the server has been lost
        if responseString == "":
            print("The connection to the server has been lost.")
            break

        response = json.loads(responseString)
        cmd = response["cmd"]

        # show the <nickname, IP, port> list of all users
        if cmd == USERS_RESPONSE:
            for user in response["users"]:
                print("Nickname:", user[0], "UserIP:", user[1], "UserPort:", user[2])
        # there is no such user of the <nickname>
        elif cmd == WHISPER_NO_SUCH_USER:
            print("Cannot whisper. No such user exists.")
        # cannot whisper myself
        elif cmd == WHISPER_MYSELF:
            print("Cannot whisper myself.")
        # whisper to <nickname>
        elif cmd == WHISPER_SUCCESS:
            print("Whispering succeeded.")
        # all other client will know when a client has disconnected from server
        elif cmd == EXIT_BROADCAST:
            print('"' + response["nickname"] + '"', "has left.")
            print("There are", response["userCount"], "users in the chatroom.")
        # show server's and client's software version
        elif cmd == VERSION_RESPONSE:
            print("Server version :", response["serverVersion"])
            print("Client version :", CLIENT_VERSION)
        # cannot change to the <nickname> because the <nickname> is userd by another user
        elif cmd == RENAME_DUPLICATE_NICKNAME:
            print("That nickname is used by another user. Cannot change to the nickname.")
        # change client nickname
        elif cmd == RENAME_SUCCESS:
            newNickname = response["newNickname"]
            print("Your nickname is changed to", newNickname)
            iClientSocket.nickname = newNickname
        # show RTT (Round Trip Time) from the client to the server and back
        elif cmd == RTT_RESPONSE:
            print("Round Trip Time :", time.time() * 1000 - response["beginTime"], "ms.")
        # show chat and chatter's nickname
        elif cmd == CHAT_RESPONSE:
            print(response["from"] + ">", response["msg"])
        # when a new user enters to the chatroom
        elif cmd == NEW_USER_ENTERS:
            print('"' + response["nickname"] + '"', "has entered.")
            print("There are", response["userCount"], "users in the chatroom.")
        else:
            print("Invalid request command. Command:", cmd)

    # if the server disconnects client, or connection to the server has been lost
    # exit the receiving thread and main thread (= exit the client process)
    clientSocket.close()
    iClientSocket.clientSocket = None


# function for sending thread
def send(iClientSocket):
    clientSocket = iClientSocket.clientSocket
    try:
        while True:
            # user input command or chat
            userInput = input(iClientSocket.nickname + "> ")

            # if input is empty, try again
            if userInput == "":
                continue

            request = {}

            # send request to the server. there are 7 kinds of requests.
            # - USERS : show the <nickname, IP, port> list of all users
            # - WHISPER : whisper to <nickname>
            # - EXIT : disconnect from server, and quit client process
            # - VERSION : show server's software version (and client software version)
            # - RENAME : change client nickname
            # - RTT : show RTT(Round Trip Time) from the client to the server and back
            # - CHAT : send a chat to all users in the chatroom
            if userInput.startswith("\\users"):
                request["cmd"] = USERS
                clientSocket.send(json.dumps(request).encode("utf-8"))
            elif userInput.startswith("\\wh"):
                userInput = userInput.split()
                request["cmd"] = WHISPER
                request["to"] = userInput[1]
                request["msg"] = " ".join(userInput[2:])
                clientSocket.send(json.dumps(request).encode("utf-8"))
            elif userInput.startswith("\\exit"):
                clientSocket.send(json.dumps({"cmd": EXIT}).encode("utf-8"))
                break
            elif userInput.startswith("\\version"):
                request["cmd"] = VERSION
                clientSocket.send(json.dumps(request).encode("utf-8"))
            elif userInput.startswith("\\rename"):
                userInput = userInput.split()
                newNickname = userInput[1]
                request["cmd"] = RENAME
                request["newNickname"] = newNickname
                clientSocket.send(json.dumps(request).encode("utf-8"))
            elif userInput.startswith("\\rtt"):
                request["cmd"] = RTT
                request["beginTime"] = time.time() * 1000
                clientSocket.send(json.dumps(request).encode("utf-8"))
            # Undefined command
            elif userInput.startswith("\\"):
                print("Unknown command. Please input again.")
            else:
                request["cmd"] = CHAT
                request["msg"] = userInput
                clientSocket.send(json.dumps(request).encode("utf-8"))

    except Exception as e:
        print(e)


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

# client state
serverName = "nsl2.cau.ac.kr"
serverPort = 20825
clientPort = 0
nickname = sys.argv[1]
clientSocket = connectServer(serverName, serverPort, clientPort, nickname)

# if a client failed to connect to the server, exit this process
if clientSocket == None:
    print("Cannot connect to the server")
    sys.exit()

iClientSocket = ClientSocket(clientSocket, nickname)  # instance of the ClientSocket

# thread which is receiving all messages from the server
# when the main thread exit, the receiving thread also exits
receiveThread = threading.Thread(target=receive, args=(iClientSocket,))
receiveThread.daemon = True
receiveThread.start()

# thread which is sending a message to the server
# when the main thread exit, the sending thread also exits
sendThread = threading.Thread(target=send, args=(iClientSocket,))
sendThread.daemon = True
sendThread.start()

# main thread checks whether the client socket is closed every 1 seconds
try:
    while iClientSocket.clientSocket != None:
        time.sleep(1)
# when Ctrl+C pressed in the client process
# the client sends exit message to the server, close the client socket,
except KeyboardInterrupt:
    clientSocket.send(json.dumps({"cmd": EXIT}).encode("utf-8"))
    clientSocket.close()

# print out “adios~” , and exit
print("\nadios~")
