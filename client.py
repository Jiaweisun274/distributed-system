import socket
import threading
import sys

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if message:
                print("\n" + message)
        except Exception as e:
            print("You have been disconnected from the server.")
            sock.close()
            break

def send_messages(sock):
    commands = {
        '1': 'Set Nickname',
        '2': 'Join a Channel',
        '3': 'Send a Public Message',
        '4': 'Send a Private Message',
        '5': 'Quit'
    }

    def prompt():
        print("\n=== Chat Menu ===")
        for key, value in commands.items():
            print(f"{key}: {value}")
        return input("Select an option: ")

    while True:
        option = prompt()

        if option == '1':
            nickname = input("Enter your nickname: ")
            sock.send(f"/nick {nickname}".encode('utf-8'))
        elif option == '2':
            channel = input("Enter channel name: ")
            sock.send(f"/join {channel}".encode('utf-8'))
        elif option == '3':
            message = input("Enter your message: ")
            sock.send(message.encode('utf-8'))
        elif option == '4':
            recipient = input("Enter recipient's nickname: ")
            message = input("Enter your message: ")
            sock.send(f"/pm {recipient} {message}".encode('utf-8'))
        elif option == '5':
            sock.send("/quit".encode('utf-8'))
            print("Disconnecting from the server...")
            sock.close()
            sys.exit()
        else:
            print("Invalid option, please try again.")

def start_client(server_ip, server_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((server_ip, server_port))
        print("Connected to the chat server.\n")


        threading.Thread(target=receive_messages, args=(sock,), daemon=True).start()
        send_messages(sock)
    except Exception as e:
        print(f"Unable to connect to the server: {e}")
        sock.close()

if __name__ == "__main__":
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 12345
    start_client(SERVER_IP, SERVER_PORT)
