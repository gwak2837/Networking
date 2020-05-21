# 20171758 Gwak Taeuk
# ChatTCPClient.py

from socket import *
from time import *
import json
from sys import *

class InvalidServerResponse(Exception):
    pass

# try to connect to server(serverName:serverPort) by TCP
def connectTCP(serverName, serverPort, clientPort):
    # create TCP client socket following IPv4 at clientPort
    clientSocket = socket(AF_INET, SOCK_STREAM)

    # set connetion timeout 10 seconds
    clientSocket.settimeout(10)

    counter = 0
    chatroomInfo = None
    while True:
        # if the times of connecting to server by TCP is more than 10, close the socket and exit this process
        if(counter > 10):
            clientSocket.close()
            exit()
        try:
            # connect to server(serverName:serverPort)
            clientSocket.connect((serverName, serverPort))

            # send client information to the server
            clientInfo = {
                'IP': clientSocket.getsockname()[0],
                'port': clientPort,
                'nickname': nickname
            }
            request = json.dumps(clientInfo)
            clientSocket.send(request.encode('utf-8'))

            # receive response from the server
            response = clientSocket.recv(4).decode('utf-8')
            if(response == CHATROOM_FULL):
                print('full. cannot connect')
                clientSocket.close()
                exit()
            elif(response == INVALID_NICKNAME):
                print('that nickname is used by another user or too long. connot connect')
                clientSocket.close()
                exit()
            elif(response == CHATROOM_ENTRY_SUCCESS):
                print('Valid nickname')
            else:
                print('Invalid response:', response)
                raise InvalidServerResponse

            # get server IP address from the server
            response = clientSocket.recv(128).decode('utf-8')
            chatroomInfo = json.loads(response)

            # print a greeting
            print('welcome', nickname, 'to cau-netclass chatroom at', chatroomInfo['serverIP'], chatroomInfo['serverPort'], end='.')
            print('You are', chatroomInfo['userCount'], 'th user.')

            break

        # gaierror: Invalid address of server
        except gaierror:
            print('gaierror: Invalid address of server')
            clientSocket.close()
            exit()
        # ConnectionRefusedError: Connection is refused by remote host
        except ConnectionRefusedError:
            print('ConnectionRefusedError: Connection is refused by remote host')
            sleep(1)
            counter += 1
        # ConnectionAbortedError: Connection is aborted by remote host
        except ConnectionAbortedError:
            print('ConnectionAbortedError: Connection is aborted by remote host')
            sleep(1)
            counter += 1
        # TimeoutError: No response from server
        except TimeoutError:
            print('TimeoutError: No response from server')
            clientSocket.close()
            exit()
        # timeout: No response from server
        except timeout:
            print('timeout: No response from server')
            clientSocket.close()
            exit()

    return clientSocket

def isValidNickname(nickname):
    if(len(nickname) > 32):
        print('Your nickname is too long. The name cannot be longer than 32 characters')
        return False 
    return True


# get user nickname from the command line arguments
nickname = argv[1]
if(not isValidNickname(nickname)):
    exit()

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

# try to connect to server by TCP
# for the client socket, you should use null(0) port number
serverName = 'localhost'
serverPort = 21758
clientPort = 0
clientSocket = connectTCP(serverName, serverPort, clientPort)

# list of banned(taboo) words
tabooWords = ['i hate professor']

# Unless explicitly terminated by option 5 or ‘Ctrl-C’, client should not terminate and should repeat the menu
while True:
    try:
        # receive user input
        userInput = input(nickname + '> ')

        # check if there are any taboo words in the input value
        for tabooWord in tabooWords:
            if(userInput.lower().find(tabooWord) > 0):
                break

        # show the <nickname, IP, port> list of all users
        if(userInput.startswith('\\users')):
            request = json.dumps({"cmd": CLIENT_USERS})
            clientSocket.send(request.encode('utf-8'))
            response = clientSocket.recv(1024).decode('utf-8')
            usersInfo = json.loads(response)
            for user in usersInfo:
                print('Nickname:', user, 'IP:', usersInfo[user][0], 'Port:', usersInfo[user][1])
        
        elif(userInput.startswith('\\wh')):
            userInput = userInput.split()
            whisperTo = userInput[1]
            msg = ' '.join(userInput[2:])
            requestJson = {
                "cmd": CLIENT_WHISPER,
                'whisperTo': whisperTo,
                'msg': msg
            }
            request = json.dumps(requestJson)
            clientSocket.send(request.encode('utf-8'))
        
        # disconnect from server, and quit
        elif(userInput.startswith('\\exit')):
            break
        #
        elif(userInput.startswith('\\version')):
            request = json.dumps({"cmd": CLIENT_VERSION})
            clientSocket.send(request.encode('utf-8'))
        #
        elif(userInput.startswith('\\rename')):
            #
            userInput = userInput.split()
            newNickname = userInput[1]
            if(not isValidNickname(newNickname)):
                continue
            requestJson = {
                "cmd": CLIENT_RENAME,
                "newNickname": newNickname
            }
            request = json.dumps(requestJson)
            clientSocket.send(request.encode('utf-8'))
            #
            response = clientSocket.recv(16).decode('utf-8')
            if(response == INVALID_NICKNAME):
                print('that nickname is used by another user or too long. cannot change')
                continue
            elif(response == VALID_NICKNAME):
                print('your nickname is changed to', newNickname)
                nickname = newNickname
            else:
                print('Invalid response:', response)
                raise InvalidServerResponse
        #
        elif(userInput.startswith('\\rtt')):
            request = json.dumps({"cmd": CLIENT_RTT})
            start = time() * 1000
            clientSocket.send(request.encode('utf-8'))
            response = clientSocket.recv(2).decode('utf-8')
            end = time() * 1000
            if(response == CLIENT_RTT_REPLY):
                print('Round Trip Time:', end - start, 'ms')
            else:
                print('Invalid response:', response)
                raise InvalidServerResponse
        #
        else:
            request = json.dumps({"cmd": CLIENT_CHAT})
            clientSocket.send(request.encode('utf-8'))

    # when the user enters ‘Ctrl-C’, the program should not show any error messages
    except KeyboardInterrupt:      
        break
    # when the server socket closed?
    except (ConnectionResetError, BrokenPipeError):
        print('ConnectionResetError: Connection is reset by remote host')
        # try to reconnect to server by TCP
        # 
        # 
        clientSocket.close()
        clientSocket = connectTCP(serverName, serverPort, clientPort)
    # when connection timed out
    except timeout:
        print('timeout: Connection timed out')
    # other exception
    except Exception as e:
        print(e)

    print()

# Send a request to the server to terminate the connection
# the program should print out “adios~” and exit
request = json.dumps({"cmd": CLIENT_EXIT})
clientSocket.send(request.encode('utf-8'))
clientSocket.close()
print('\nadios~')
