from socket import *
from time import *
import pickle
from sys import exit


# try to connect to server(serverName:s~erverPort) by TCP
def connect_TCP(server_name, server_port, client_port):
    # create TCP client socket following IPv4 at clientPort
    client_socket = socket(AF_INET, SOCK_STREAM)

    """
    # handle OSError: [Errno 98] Address already in use
    while True:
        try:
            clientSocket.bind(('', clientPort))
            break
        except OSError:
            clientPort += 10000
            if(clientPort > 60000):
                print('OSError: [Errno 98] Address already in use')
                exit()
    """

    # set connetion timeout 10 seconds
    client_socket.settimeout(10)

    counter = 0
    while True:
        # if the times of connecting to server by TCP is more than 10, close the socket and exit this process
        if counter > 10:
            client_socket.close()
            exit()
        # try to connect to server(serverName:serverPort)
        try:
            client_socket.connect((server_name, server_port))
            break
        # gaierror: Invalid address of server
        except gaierror:
            print("gaierror: Invalid address of server")
            client_socket.close()
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
            client_socket.close()
            exit()
        # timeout: No response from server
        except timeout:
            print("timeout: No response from server")
            client_socket.close()
            exit()

    return client_socket


# try to connect to server by TCP
# for the client socket, you should use null(0) port number
server_name = "localhost"
server_port = 21758
client_port = 0
clientSocket = connect_TCP(server_name, server_port, client_port)

# print the port number of the socket
print("The client socket was created on port", clientSocket.getsockname()[1])

# Unless explicitly terminated by option 5 or ‘Ctrl-C’, client should not terminate and should repeat the menu
while True:
    try:
        # print menu
        print("<Menu>")
        print("1) convert text to UPPER-case")
        print("2) get my IP address and port number")
        print("3) get server time ")
        print("4) get server running time")
        print("5) exit")

        # receive user input
        command = input("Input option: ")
        jsonData = {"command": command}

        # convert text to UPPER-case letters
        if command == "1":
            # if the user selects option 1, the client also takes user keyboard input
            message = input("Input lowercase sentence: ")
            jsonData["message"] = message
            request = pickle.dumps(jsonData)

            # Sent time should be measured immediately before sending the command
            start = time() * 1000
            # Client then sends the command number and message together to the server
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            # Receiving time should be measured immediately after receiving the reply
            end = time() * 1000

            # print out the reply text string
            print("Reply from server:", response)
            # duration between when the client sent the command to the server and when the client received the reply from the server
            print("Response time:", end - start, "ms")
        # ask the server what is the IP address and port number of the client (myself)
        elif command == "2":
            request = pickle.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            end = time() * 1000

            # make response from server into python dictionary data type
            address = pickle.loads(response)

            print("Reply from server:", "IP =", address["IP"] + ",", "port =", address["Port"])
            print("Response time:", end - start, "ms")
        # ask the server what the current time on the server is.
        elif command == "3":
            request = pickle.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            end = time() * 1000

            print("Reply from server:", "time =", response)
            print("Response time:", end - start, "ms")
        # ask the server program how long it has been running for since it started
        elif command == "4":
            request = pickle.dumps(jsonData)

            start = time() * 1000
            clientSocket.send(request.encode())
            response = clientSocket.recv(2048).decode()
            end = time() * 1000

            print("Reply from server:", "run time =", response)
            print("Response time:", end - start, "ms")
        # exit client program
        elif command == "5":
            # the program should print out “Bye bye~” and exit
            print("Bye bye~")
            break

    # when the user enters ‘Ctrl-C’, the program should not show any error messages
    except KeyboardInterrupt:
        print("\nBye bye~")
        break
    # when the server socket closed?
    except (ConnectionResetError, BrokenPipeError):
        print("ConnectionResetError: Connection is reset by remote host")
        # try to reconnect to server by TCP
        clientSocket.close()
        clientSocket = connect_TCP(server_name, server_port, client_port)
    # when connection timed out
    except timeout:
        print("timeout: Connection timed out")
    # other exception
    except Exception as e:
        print(e)

    print()

clientSocket.close()
