import socket
import threading

clients = {}
channels = {"general": set()} 

def broadcast(message, channel, exclude_socket=None):
    for client in channels[channel]:
        if client != exclude_socket:
            try:
                formatted_message = f"[{channel}] {message}"
                client.send(formatted_message.encode('utf-8'))
            except:
                client.close()
                remove_client(client)

def remove_client(client):
    nickname = clients[client]['nickname']
    for channel in channels.values():
        channel.discard(client)
    clients.pop(client, None)
    print(f"{nickname} has disconnected")

def handle_private_message(sender_socket, recipient_nickname, message):
    sender_channel = clients[sender_socket]['channel']
    recipient_socket = None
    for client, info in clients.items():
        if info["nickname"] == recipient_nickname and info["channel"] == sender_channel:
            recipient_socket = client
            break
    if recipient_socket:
        try:
            full_message = f"[{sender_channel}] PM from {clients[sender_socket]['nickname']}: {message}"
            recipient_socket.send(full_message.encode('utf-8'))
        except:
            remove_client(recipient_socket)
    else:
        sender_socket.send(f"User '{recipient_nickname}' not found in your channel.".encode('utf-8'))

def handle_client(client):
    clients[client] = {"nickname": "Anonymous", "channel": "general"} 
    channels["general"].add(client)
    while True:
        try:
            message = client.recv(1024).decode('utf-8')
            if message.startswith("/nick"):
                _, nickname = message.split(maxsplit=1)
                clients[client]["nickname"] = nickname
                client.send("Nickname set successfully.".encode('utf-8'))
            elif message.startswith("/join"):
                _, channel_name = message.split(maxsplit=1)
                if channel_name not in channels:
                    channels[channel_name] = set()
                current_channel = clients[client]["channel"]
                channels[current_channel].discard(client)
                channels[channel_name].add(client)
                clients[client]["channel"] = channel_name
                client.send(f"You joined {channel_name} channel.".encode('utf-8'))
            elif message.startswith("/pm"):
                _, recipient_nickname, *msg_parts = message.split(maxsplit=2)
                pm_message = ' '.join(msg_parts)
                handle_private_message(client, recipient_nickname, pm_message)
            elif message.startswith("/quit"):
                client.send("You have disconnected.".encode('utf-8'))
                remove_client(client)
                client.close()
                break
            else:
                # Public message to the current channel
                channel = clients[client]["channel"]
                broadcast(f"{clients[client]['nickname']}: {message}", channel, client)
        except:
            remove_client(client)
            client.close()
            break

def start_server(host='localhost', port=12345):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen()
    print(f"Chat server started on {host}:{port}")

    while True:
        client, addr = server_socket.accept()
        print(f"Connected with {addr}")
        thread = threading.Thread(target=handle_client, args=(client,))
        thread.start()

if __name__ == "__main__":
    start_server()
