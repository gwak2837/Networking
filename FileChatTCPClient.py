# 20171758 Gwak Taeuk
# ChatTCPClient.py

from socket import *
from time import *
from sys import *
from threading import Thread
from threading import Lock
from hashlib import sha256
import pickle
import math


class InvalidServerResponse(Exception):
    pass


class ClientInfo:
    def __init__(self, nickname, clientSocket):
        self.nickname = nickname
        self.clientSocket = clientSocket
        self.lock = Lock()

    def setNickname(self, newNickname):
        self.lock.acquire()
        self.nickname = newNickname
        self.lock.release()


# try to connect to server(serverName:serverPort) by TCP
def connectTCP(serverName, serverPort, clientPort):
    clientSocket = socket(AF_INET, SOCK_STREAM)  # create TCP client socket following IPv4 at clientPort
    clientSocket.settimeout(10)  # set connetion timeout 10 seconds
    counter = 0
    while True:
        # if the times of connecting to server by TCP is more than 10, close the socket and exit this process
        if counter > 10:
            clientSocket.close()
            exit()
        try:
            clientSocket.connect((serverName, serverPort))  # connect to server(serverName:serverPort)
            break
        # gaierror: Invalid address of server
        except gaierror:
            print("gaierror: Invalid address of server")
            clientSocket.close()
            exit()
        # ConnectionRefusedError: Connection is refused by remote host
        except ConnectionRefusedError:
            print("ConnectionRefusedError: Connection is refused by remote host")
            sleep(1)
            counter += 1
        # ConnectionAbortedError: Connection is aborted by remote host
        except ConnectionAbortedError:
            print("ConnectionAbortedError: Connection is aborted by remote host")
            sleep(1)
            counter += 1
        # TimeoutError: No response from server
        except TimeoutError:
            print("TimeoutError: No response from server")
            clientSocket.close()
            exit()
        # timeout: No response from server
        except timeout:
            print("timeout: No response from server")
            clientSocket.close()
            exit()

    return clientSocket


def receive(clientInfo):
    # client state variable
    clientSocket = clientInfo.clientSocket
    filesDictionary = {}  # { fileHash: {fileName: "", filePieceCount: 0, filePieces: []}, ... }

    while True:
        try:
            response = clientSocket.recv(1024)
        except timeout:
            continue

        # when the connection disconnects for the TCP case, or when server disconnects
        if response == b"":
            print('Response = ""')
            clientSocket.close()
            clientInfo.clientSocket = None
            break

        response = pickle.loads(response)
        cmd = response["cmd"]

        if cmd == USERS_RESPONSE:
            users = response["users"]
            for user in users:
                print("Nickname:", user[0], "IP:", user[1], "Port:", user[2])
        elif cmd == WHISPER_NO_USER:
            print("No such user exists.")
        elif cmd == WHISPER_MYSELF:
            print("Cannot whisper myself.")
        elif cmd == WHISPER_SUCCESS:
            print("Whispering succeeded.")
        elif cmd == EXIT_RESPONSE:
            print(response["nickname"], "is disconnected. There are", response["userCount"], "users in the chat room.")
        elif cmd == VERSION_RESPONSE:
            print("Server version :", response["version"])
            print("Client version :", CLIENT_VERSION)
        elif cmd == RENAME_INVALID_NICKNAME:
            print("That nickname is used by another user or too long. Cannot change to the nickname.")
        elif cmd == RENAME_SUCCESS:
            newNickname = response["nickname"]
            print("Your nickname is changed to", newNickname)
            clientInfo.setNickname(newNickname)
        elif cmd == RTT_RESPONSE:
            print("Round Trip Time :", time() * 1000 - response["startTime"], "ms.")
        elif cmd == CHAT_RESPONSE:
            print(response["from"] + ">", response["msg"])
        elif cmd == FILE_TRANSFER_WHISPER_NO_USER:
            print("No such user exists.")
        elif cmd == FILE_TRANSFER_WHISPER_MYSELF:
            print("Cannot send a file to myself.")
        elif cmd == FILE_TRANSFER_RESPONSE:
            if "whisperTo" in response:
                print(response["sender"], "is sending file", response["fileName"], "to", response["whisperTo"])
            else:
                print(response["sender"], "is sending file", response["fileName"])

            # identify files by file hash
            # if the file hash is new, create a new dictionary entry
            fileHash = response["fileHash"]
            if fileHash not in filesDictionary:
                filesDictionary[fileHash] = {
                    "fileName": response["fileName"],
                    "sender": response["sender"],
                    "filePieceCount": 0,
                    "filePieces": [0 for i in range(response["totalFilePieces"])],
                }

            # save the file piece
            # when the entire file piece is downloaded without any error, save it as a file
            fileInfo = filesDictionary[fileHash]
            if (
                fileInfo["filePieces"][response["filePieceNo"]] == 0
                and fileInfo["fileName"] == response["fileName"]
                and len(fileInfo["filePieces"]) == response["totalFilePieces"]
            ):
                fileInfo["filePieces"][response["filePieceNo"]] = response["filePiece"]
                fileInfo["filePieceCount"] += 1
                if fileInfo["filePieceCount"] == len(fileInfo["filePieces"]):
                    binaryFile = b"".join(fileInfo["filePieces"])
                    if sha256(binaryFile).digest() == fileHash:
                        if "whisperTo" in response:
                            filename = (
                                "wsend_" + fileInfo["sender"] + "_" + response["whisperTo"] + "_" + fileInfo["fileName"]
                            )
                        else:
                            filename = (
                                "fsend_" + fileInfo["sender"] + "_" + clientInfo.nickname + "_" + fileInfo["fileName"]
                            )
                        with open(filename, "wb") as f:
                            f.write(binaryFile)
                        print("File", filename, "received from", fileInfo["sender"])
                        del fileInfo
                    else:
                        print("Invalid file hash. The file data might be invalid")
            # the file piece is duplicate (not expected case)
            else:
                print("Unexpected case.")

        else:
            print("Invalid response:", cmd)


def send(clientInfo):
    # list of banned(taboo) words
    tabooWords = ["i hate professor"]

    # Unless explicitly terminated by option 5 or ‘Ctrl-C’, client should not terminate and should repeat the menu
    clientSocket = clientInfo.clientSocket
    while True:
        userInput = input(clientInfo.nickname + "> ")  # receive user input
        if userInput == "":
            continue

        # check if there are any taboo words in the input value
        if not isValidMessage(userInput, tabooWords):
            print("Invalid message. Please write a message again.")
            continue

        request = {}
        try:
            # show the <nickname, IP, port> list of all users
            if userInput.startswith("\\users"):
                request["cmd"] = USERS
                clientSocket.send(pickle.dumps(request, protocol=4))
            # whisper to <nickname>
            elif userInput.startswith("\\wh"):
                userInput = userInput.split()
                request["cmd"] = WHISPER
                request["whisperTo"] = userInput[1]
                request["msg"] = " ".join(userInput[2:])
                clientSocket.send(pickle.dumps(request, protocol=4))
            # disconnect from server, and quit
            elif userInput.startswith("\\exit"):
                # send a request to the server to terminate the connection and close the client socket
                clientSocket.send(pickle.dumps({"cmd": EXIT}, protocol=4))
                break
            # show server's software version (and client software version)
            elif userInput.startswith("\\version"):
                request["cmd"] = VERSION
                clientSocket.send(pickle.dumps(request, protocol=4))
            # change client nickname
            elif userInput.startswith("\\rename"):
                # send a request to the server
                userInput = userInput.split()
                newNickname = userInput[1]
                if not isValidNickname(newNickname):
                    print("Invalid nickname. Please try again.")
                    continue
                request["cmd"] = RENAME
                request["newNickname"] = newNickname
                clientSocket.send(pickle.dumps(request, protocol=4))
            # show RTT(Round Trip Time) from the client to the server and back
            elif userInput.startswith("\\rtt"):
                request["cmd"] = RTT
                request["startTime"] = time() * 1000
                clientSocket.send(pickle.dumps(request, protocol=4))
            #
            elif userInput.startswith("\\fsend"):
                userInput = userInput.split()
                try:
                    with open(userInput[1], "rb") as f:
                        binaryData = f.read()
                except FileNotFoundError as e:
                    print(e)
                    continue

                totalFilePieces = math.ceil(len(binaryData) / 1024)
                request["cmd"] = FILE_TRANSFER_ALL
                request["sender"] = clientInfo.nickname
                request["fileHash"] = sha256(binaryData).digest()
                request["fileName"] = userInput[1]
                request["totalFilePieces"] = totalFilePieces

                for filePieceNo in range(totalFilePieces):
                    print(filePieceNo)
                    request["filePieceNo"] = filePieceNo
                    request["filePiece"] = binaryData[filePieceNo * 1024 : (filePieceNo + 1) * 1024]
                    clientSocket.send(pickle.dumps(request, protocol=4))
            #
            elif userInput.startswith("\\wsend"):
                # open file and get binary data of file
                userInput = userInput.split()
                try:
                    with open(userInput[1], "rb") as f:
                        binaryData = f.read()
                except FileNotFoundError as e:
                    print(e)
                    continue

                totalFilePieces = 1
                request["cmd"] = FILE_TRANSFER_WHISPER
                request["sender"] = clientInfo.nickname
                request["fileHash"] = sha256(binaryData).digest()
                request["fileName"] = userInput[1]
                request["whisperTo"] = userInput[2]
                request["totalFilePieces"] = totalFilePieces
                request["filePieceNo"] = 0
                request["filePiece"] = binaryData
                clientSocket.send(pickle.dumps(request, protocol=4))
            # undefined command
            elif userInput.startswith("\\"):
                print("Undefined command")
            # send a chat to the server
            else:
                request["cmd"] = CHAT
                request["msg"] = userInput
                clientSocket.send(pickle.dumps(request, protocol=4))
        # handle `IndexError` of `userInput`
        except IndexError as e:
            print(e)

        sleep(0.5)
        print()


def isValidNickname(nickname):
    if len(nickname) > 32:
        print("Your nickname is too long. The name cannot be longer than 32 characters")
        return False
    return True


def isValidMessage(message, tabooWords):
    for tabooWord in tabooWords:
        if False:  # turn off filtering taboo words on client side
            # if(message.lower().find(tabooWord) > 0):  # turn on filtering taboo words on client side
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

# get user nickname from the command line arguments
nickname = argv[1]
if not isValidNickname(nickname):
    exit()

# try to connect to server by TCP
# for the client socket, you should use null(0) port number
serverName = "localhost"
serverPort = 21758
clientPort = 0
clientSocket = connectTCP(serverName, serverPort, clientPort)

try:
    # send client nickname to the server
    request = {}
    request["cmd"] = PRECONNECT
    request["nickname"] = nickname
    clientSocket.send(pickle.dumps(request, protocol=4))

    # receive response from the server
    response = pickle.loads(clientSocket.recv(1024))
    cmd = response["cmd"]
    if cmd == PRECONNECT_CHATROOM_FULL:
        print("Chatroom is full. Cannot enter the chatroom.")
        clientSocket.close()
        exit()
    elif cmd == PRECONNECT_INVALID_NICKNAME:
        print("That nickname is used by another user or too long. Cannot connect to the server.")
        clientSocket.close()
        exit()
    elif cmd == PRECONNECT_SUCCESS:
        print("Welcome", nickname, "to cau-netclass chatroom at", response["serverIP"], response["serverPort"])
        print("You are", response["userCount"], "th user.")
    else:
        print("Invalid response:", response)
        raise InvalidServerResponse

    clientInfo = ClientInfo(nickname, clientSocket)

    # thread which is receiving all messages from the server
    receiveThread = Thread(target=receive, args=(clientInfo,))
    receiveThread.daemon = True
    receiveThread.start()

    # thread which is sending a message to the server
    sendThread = Thread(target=send, args=(clientInfo,))
    sendThread.daemon = True
    sendThread.start()

    while clientInfo.clientSocket != None:
        sleep(0.5)

except ConnectionResetError:
    print("ConnectionResetError: Connection is reset by remote host")
except BrokenPipeError:
    print("BrokenPipeError: Connection disconnected while processing recv() or send()")
# when the user enters ‘Ctrl-C’, the program should not show any error messages
except KeyboardInterrupt:
    # send a request to the server to terminate the connection and close the client socket
    clientSocket.send(pickle.dumps({"cmd": EXIT}, protocol=4))
    clientSocket.close()
# other exception
except Exception as e:
    print(e)

# the program should print out “adios~” and exit
print("\nadios~")
