import socket
import threading

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode('utf-8')
            if message:
                print(message)
            else:
                break
        except:
            print("You have been disconnected from the server.")
            break

def send_messages(sock):
    while True:
        message = input()
        try:
            sock.send(message.encode('utf-8'))
        except:
            print("Unable to send the message. You may have been disconnected.")
            break

if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('127.0.0.1', 65432))
        print("Connected to the server.")
        threading.Thread(target=receive_messages, args=(sock,)).start()
        send_messages(sock)