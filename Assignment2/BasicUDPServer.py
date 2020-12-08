# 20170825 Seo Shinak
# BasicUDPServer.py

from socket import *
from time import *
import json

# measure the server starting time
start = time()

# create TCP socket that following IPv4 on the port #10825
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverPort = 30825
serverSocket.bind(('', serverPort))

# print the port number of the socket
print("The server socket was created on port", serverSocket.getsockname()[1])

try:
    while True:
        # Server will receive the command and reply with an appropriate response based on the command
        request, clientAddress = serverSocket.recvfrom(2048)
        requestJson = json.loads(request.decode())
        command = requestJson['command']

        print('Connection requested from', clientAddress)

        # convert text to UPPER-case letters
        if(command == '1'):
            print('Command', command)
            response = requestJson['message'].upper()
            serverSocket.sendto(response.encode(), clientAddress)
        # tell the client what the IP address and port number of the client is
        elif(command == '2'):
            print('Command', command)
            address = {
                "IP": clientAddress[0],
                "Port": clientAddress[1]
            }
            response = json.dumps(address)
            serverSocket.sendto(response.encode(), clientAddress)
        # tell the client what the current time on the server is
        elif(command == '3'):
            print('Command', command)
            serverSocket.sendto(strftime(
                '%H-%M-%S', localtime(time())).encode(), clientAddress)
        # tell the client how long it (server program) has been running for
        elif(command == '4'):
            print('Command', command)
            serverSocket.sendto(strftime(
                '%H-%M-%S', gmtime(time() - start)).encode(), clientAddress)
        # test time out
        elif(command == '6'):
            print('Command', command)
            sleep(15)
        # test buffer overflow
        elif(command == '7'):
            print('Command', command)
            response = requestJson['message']
            serverSocket.sendto(response.encode(), clientAddress)
        else:
            continue
except KeyboardInterrupt:
    print('\nBye bye~')

serverSocket.close()
