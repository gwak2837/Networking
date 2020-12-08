import socket
import time
import pickle
from sys import exit


# 매개변수에 해당하는 TCP 소켓에 접속한다.
def connect_to_tcp_socket(host, port):
    # socket.AF_INET : IPv4
    # socket.SOCK_STREAM : TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # timeout 설정: 10초
    client_socket.settimeout(10)

    counter = 0
    while True:
        if counter > 10:
            print("서버로 연결 요청을 10번 이상 보냈지만 응답이 없어요..")
            client_socket.close()
            exit()
        try:
            client_socket.connect((host, port))
            break
        # 유효하지 않은 (host, port)를 입력했을 때
        except socket.gaierror as e:
            print(e)
            client_socket.close()
            exit()
        # 서버로 연결을 요청한지 10초 이상 지났을 때
        except socket.timeout as e:
            print(e)
            time.sleep(1)
            counter += 1
        # ?
        except ConnectionAbortedError as e:
            print(e)
            time.sleep(1)
            counter += 1
        # ?
        except ConnectionRefusedError as e:
            print(e)
            time.sleep(1)
            counter += 1
        # ?
        except TimeoutError as e:
            print(e)
            time.sleep(1)
            counter += 1
        # 그 외 생각하지 못한 예외
        except Exception as e:
            print(e)
            time.sleep(1)
            counter += 1

    return client_socket


host = "localhost"
port = 10000
client_socket = connect_to_tcp_socket(host, port)

# 클라이언트 소켓이 생성된 곳을 출력한다.
print(f"Host: {client_socket.getsockname()[0]}, Port: {client_socket.getsockname()[1]}")

while True:
    try:
        # 각 요청 번호의 설명을 출력한다.
        print("<요청>")
        print("1) 문자열을 대문자로 변경해서 출력")
        print("2) 클라이언트 소켓의 IP 주소와 포트 번호 출력")
        print("3) 서버 현재 시간 출력")
        print("4) 서버 실행 시간 출력")
        print("5) 클라이언트 종료")

        # 사용자로부터 요청 번호를 입력받는다.
        command = input("요청 번호를 입력하세요: ")
        request = {"command": command}

        # 문자열을 모두 대문자로 바꾸는 요청
        if command == "1":
            # 사용자로부터 문자열을 입력받는다.
            message = input("대문자로 변환할 문자열 입력: ")
            request["message"] = message
            binary_stream = pickle.dumps(request)

            # 요청 번호와 문자열을 바이트로 변환해서 서버로 전송한다.
            start = time.time() * 1000
            client_socket.send(binary_stream)
            response = pickle.loads(client_socket.recv(2048))
            end = time.time() * 1000

            # 서버로부터 받은 응답을 출력한다.
            print(f"서버로부터 받은 응답: {response}")

            # 클라이언트에서 측정한 RTT를 출력한다.
            print(f"RTT: {end - start} ms")

        # ask the server what is the IP address and port number of the client (myself)
        elif command == "2":
            binary_stream = pickle.dumps(request)

            start = time() * 1000
            client_socket.send(binary_stream.encode())
            response = client_socket.recv(2048).decode()
            end = time() * 1000

            # make response from server into python dictionary data type
            address = pickle.loads(response)

            print("Reply from server:", "IP =", address["IP"] + ",", "port =", address["Port"])
            print("Response time:", end - start, "ms")
        # ask the server what the current time on the server is.
        elif command == "3":
            binary_stream = pickle.dumps(request)

            start = time() * 1000
            client_socket.send(binary_stream.encode())
            response = client_socket.recv(2048).decode()
            end = time() * 1000

            print("Reply from server:", "time =", response)
            print("Response time:", end - start, "ms")
        # ask the server program how long it has been running for since it started
        elif command == "4":
            binary_stream = pickle.dumps(request)

            start = time() * 1000
            client_socket.send(binary_stream.encode())
            response = client_socket.recv(2048).decode()
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
        client_socket.close()
        client_socket = connect_to_tcp_socket(host, port)
    # when connection timed out
    except socket.timeout:
        print("timeout: Connection timed out")
    # other exception
    except Exception as e:
        print(e)

    print()

client_socket.close()
