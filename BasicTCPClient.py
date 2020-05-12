# 20171758 Gwak Taeuk
# BasicTCPClient.py

from socket import *
from time import *
import json
from sys import exit


# try to connect to server(serverName:serverPort) by TCP
def connectTCP(serverName, serverPort, clientPort):
    # create TCP client socket following IPv4 at clientPort
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.bind(('', clientPort))

    # set connetion timeout 10 seconds
    clientSocket.settimeout(10)

    counter = 0
    while True:
        # if the times of connecting to server by TCP is more than 10, close the socket and exit this process
        if(counter > 10):
            clientSocket.close()
            exit()
        # try to connect to server(serverName:serverPort)
        try:
            clientSocket.connect((serverName, serverPort))
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


# try to connect to server by TCP
serverPort = 21758
clientPort = 31758
clientSocket = connectTCP('nsl2.cau.ac.kr', serverPort, clientPort)

# print the port number of the socket
print("The client socket was created on port", clientSocket.getsockname()[1])

# Unless explicitly terminated by option 5 or ‘Ctrl-C’, client should not terminate and should repeat the menu
while True:
    try:
        # print menu
        print('<Menu>')
        print('1) convert text to UPPER-case')
        print('2) get my IP address and port number')
        print('3) get server time ')
        print('4) get server running time')
        print('5) exit')
        print('6) test timed out')
        print('7) test buffer overflow')

        # receive user input
        command = input('Input option: ')
        jsonData = {"command": command}

        # convert text to UPPER-case letters
        if(command == '1'):
            # if the user selects option 1, the client also takes user keyboard input
            message = input('Input lowercase sentence: ')
            jsonData['message'] = message
            request = json.dumps(jsonData)

            # Sent time should be measured immediately before sending the command
            start = time() * 1000
            # Client then sends the command number and message together to the server
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            # Receiving time should be measured immediately after receiving the reply
            end = time() * 1000

            # print out the reply text string
            print('Reply from server:', response)
            # duration between when the client sent the command to the server and when the client received the reply from the server
            print('Response time:', end - start, 'ms')
        # ask the server what is the IP address and port number of the client (myself)
        elif(command == '2'):
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            end = time() * 1000

            # make response from server into python dictionary data type
            address = json.loads(response)

            print('Reply from server:', 'IP =',
                  address['IP'] + ',', 'port =', address['Port'])
            print('Response time:', end - start, 'ms')
        # ask the server what the current time on the server is.
        elif(command == '3'):
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            end = time() * 1000

            print('Reply from server:', 'time =', response)
            print('Response time:', end - start, 'ms')
        # ask the server program how long it has been running for since it started
        elif(command == '4'):
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            end = time() * 1000

            print('Reply from server:', 'run time =', response)
            print('Response time:', end - start, 'ms')
        # exit client program
        elif(command == '5'):
            # the program should print out “Bye bye~” and exit
            print('Bye bye~')
            break
        # test time out
        elif(command == '6'):
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            end = time() * 1000

            print('Reply from server:', response)
            print('Response time:', end - start, 'ms')
        # test buffer overflow
        elif(command == '7'):
            jsonData['message'] = 'abcdefghigklmn'
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(5).decode()
            end = time() * 1000

            print('Reply from server:', response)
            print('Response time:', end - start, 'ms')

    # when the user enters ‘Ctrl-C’, the program should not show any error messages
    except KeyboardInterrupt:
        print('\nBye bye~')
        break
    # when the server socket closed?
    except (ConnectionResetError, BrokenPipeError):
        print('ConnectionResetError: Connection is reset by remote host')
        # try to reconnect to server by TCP
        clientSocket.close()
        clientSocket = connectTCP('nsl2.cau.ac.kr', 10825, 20825)
    # when connection timed out
    except timeout:
        print('timeout: Connection timed out')
    # other exception
    except Exception as e:
        print(e)

    print()

clientSocket.close()
