# 20170825 Seo Shinak
# BasicUDPClient.py

from socket import *
from time import *
import json

# address of server (serverName:serverPort)
serverName = 'nsl2.cau.ac.kr'
serverPort = 30825

# create UDP client socket following IPv4 at port #40825
clientPort = 40825
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.bind(('', clientPort))

# set connetion timeout 10 seconds
clientSocket.settimeout(10)

print("The client is running on port", clientSocket.getsockname()[1])

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
            clientSocket.sendto(request.encode(), (serverName, serverPort))
            response, serverAddress = clientSocket.recvfrom(2048)
            # Receiving time should be measured immediately after receiving the reply
            end = time() * 1000

            # print out the reply text string
            print('Reply from server:', response.decode())
            # duration between when the client sent the command to the server and when the client received the reply from the server
            print('Response time:', end - start, 'ms')
        # ask the server what is the IP address and port number of the client (myself)
        elif(command == '2'):
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.sendto(request.encode(), (serverName, serverPort))
            response, serverAddress = clientSocket.recvfrom(2048)
            end = time() * 1000

            # make response from server into python dictionary data type
            address = json.loads(response.decode())

            print('Reply from server:', 'IP =',
                  address['IP'] + ',', 'port =', address['Port'])
            print('Response time:', end - start, 'ms')
        # ask the server what the current time on the server is.
        elif(command == '3'):
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.sendto(request.encode(), (serverName, serverPort))
            response, serverAddress = clientSocket.recvfrom(2048)
            end = time() * 1000

            print('Reply from server:', 'time =', response.decode())
            print('Response time:', end - start, 'ms')
        # ask the server program how long it has been running for since it started
        elif(command == '4'):
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.sendto(request.encode(), (serverName, serverPort))
            response, serverAddress = clientSocket.recvfrom(2048)
            end = time() * 1000

            print('Reply from server:', 'run time =', response.decode())
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
            clientSocket.sendto(request.encode(), (serverName, serverPort))
            response, serverAddress = clientSocket.recvfrom(2048)
            end = time() * 1000

            print('Reply from server:', response.decode())
            print('Response time:', end - start, 'ms')
        # test buffer overflow
        elif(command == '7'):
            jsonData['message'] = 'abcdefghigklmn'
            request = json.dumps(jsonData)

            start = time() * 1000
            clientSocket.sendto(request.encode(), (serverName, serverPort))
            response, serverAddress = clientSocket.recvfrom(5)
            end = time() * 1000

            print('Reply from server:', response.decode())
            print('Response time:', end - start, 'ms')

    # when the user enters ‘Ctrl-C’, the program should not show any error messages
    except KeyboardInterrupt:
        print('\nBye bye~')
        break
    # ConnectionResetError: Connection is reset by remote host
    except ConnectionResetError:
        print('ConnectionResetError: Connection is reset by remote host')
    # timeout: Connection timed out (10 seconds)
    except timeout:
        print('timeout: Connection timed out')
    # Buffer overflow, ...
    except OSError as e:
        print('OSError:', e)
    # other exception
    except Exception as e:
        print(e)

    print()

clientSocket.close()
