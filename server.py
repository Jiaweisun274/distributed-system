import socket
import threading
import json
class Client:
    def __init__(self, socket, address, username):
        self.socket = socket
        self.address = address
        self.username = username
        self.game_room = None

    def send(self, message):
        try:
            self.socket.sendall(message.encode())
        except socket.error as e:
            print(f"Error sending message to {self.username}: {e}")

class GameRoom:
    def __init__(self, title, description, question, choices, correct_answer):
        self.title = title
        self.description = description
        self.question = question
        self.choices = choices
        self.correct_answer = correct_answer
        self.clients = []
        self.messages = []  # Store messages specific to this room

    def broadcast(self, message, source=None):
        for client in self.clients:
            if client != source:
                client.send(message)

    def add_client(self, client):
        self.clients.append(client)

    def remove_client(self, client):
        self.clients.remove(client)

    def store_message(self, message):
        self.messages.append(message)

    def get_messages(self):
        return self.messages


class Server:
    # Other methods remain unchanged
    def handle_chat(self, client):
        try:
            client.send("Enter your message:")
            msg = client.socket.recv(1024).decode().strip()
            client.game_room.store_message(f"{client.username}: {msg}")  # Store message in room
            client.game_room.broadcast(f"{client.username}: {msg}", client)  # Broadcast to clients in room
        except Exception as e:
            print(f"Error during chat handling for {client.username}: {e}")


def load_user_data():
    try:
        with open("user_progress.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("No existing user data found. Starting with a new file.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from user data file: {e}")
        return {}

def save_user_data(data):
    try:
        with open("user_progress.json", "w") as file:
            json.dump(data, file, indent=4)
    except IOError as e:
        print(f"Error saving user data: {e}")

class Server:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.clients = []
        self.game_rooms = [
            GameRoom("Math Quiz", "Solve simple arithmetic problems.",
                     "What is 10 + 10?", ["10", "20", "30", "40"], 1),
            GameRoom("Capital Cities", "Guess the capital of a country.",
                     "What is the capital of France?", ["Paris", "Berlin", "Madrid", "Rome"], 0),
            GameRoom("Science Trivia", "Answer general science questions.",
                     "What is the chemical symbol for water?", ["O2", "H2O", "CO2", "NaCl"], 1),
            GameRoom("Historical Facts", "Identify significant historical events.",
                     "Who discovered America?", ["Columbus", "Vespucci", "Magellan", "Cook"], 0),
            GameRoom("Popular Culture", "Questions about popular movies and music.",
                     "Who directed 'Titanic'?", ["Spielberg", "Tarantino", "Cameron", "Scorsese"], 2),
            GameRoom("Computer Basics", "Fundamental concepts of computing.",
                     "What does 'HTTP' stand for?", ["HyperText Transfer Protocol", "HighText Tool Path", "HyperTone Transmission Protocol", "None of the above"], 0),
            GameRoom("Sports Knowledge", "Various sports rules and facts.",
                     "Which sport is known as the 'King of Sports'?", ["Tennis", "Soccer", "Basketball", "Golf"], 1)
        ]
        self.user_data = load_user_data()

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((self.host, self.port))
            sock.listen()
            print("Server started, waiting for connections...")
            while True:
                try:
                    client_socket, addr = sock.accept()
                    threading.Thread(target=self.client_handler, args=(client_socket, addr)).start()
                except socket.error as e:
                    print(f"Error accepting new connection: {e}")

    def client_handler(self, client_socket, addr):
        try:
            client_socket.send("Enter your username or 'exit' to quit:".encode())
            username = client_socket.recv(1024).decode().strip()
            if username.lower() == 'exit':
                client_socket.close()
                return
            client = Client(client_socket, addr, username)
            self.clients.append(client)

            user_progress = self.user_data.get(username, {room.title: False for room in self.game_rooms})
            self.user_data[username] = user_progress

            while True:
                if self.show_menu(client, user_progress) == 'exit':
                    break
        except Exception as e:
            print(f"Error handling client {username}: {e}")
        finally:
            client_socket.close()

    def show_menu(self, client, user_progress):
        menu = "\n".join(
            f"{i+1}. {room.title}: {room.description} ({'Passed' if user_progress.get(room.title, False) else 'Not Passed'})"
            for i, room in enumerate(self.game_rooms)
        ) + "\n0. Exit or Back to Previous Menu"
        client.send("Select a game room or exit:\n" + menu)
        choice = client.socket.recv(1024).decode().strip()
        if choice.lower() == 'exit' or choice == '0':
            client.send("Exiting the game. Goodbye!\n")
            return 'exit'
        try:
            choice = int(choice) - 1
            if choice < 0 or choice >= len(self.game_rooms):
                client.send("Invalid choice, please try again.")
                return 'continue'
            client.game_room = self.game_rooms[choice]
            client.game_room.add_client(client)
            self.interact_in_room(client, user_progress)
        except ValueError:
            client.send("Invalid input, please enter a number.")
        return 'continue'

    def interact_in_room(self, client, user_progress):
        while True:
            if not user_progress[client.game_room.title]:
                question = client.game_room.question
                choices = "\n".join(f"{idx+1}. {opt}" for idx, opt in enumerate(client.game_room.choices))
                client.send(f"{question}\n{choices}\n0. Back")
            else:
                client.send("You have already passed this question. \n0. Back")
            
            client.send("\nChoose an option: 1. Answer question, 2. Chat, 0. Back")
            option = client.socket.recv(1024).decode().strip()
            if option == '0':
                return  # Return to the main menu
            elif option == '1':
                self.handle_question(client, user_progress)
            elif option == '2':
                self.handle_chat(client)

    def handle_question(self, client, user_progress):
        try:
            client.send("Select the correct answer number:")
            user_choice = int(client.socket.recv(1024).decode().strip()) - 1
            if client.game_room.check_answer(user_choice):
                client.send("Correct answer! You have passed this room.")
                user_progress[client.game_room.title] = True
                save_user_data(self.user_data)
            else:
                client.send("Wrong answer, try again!")
        except Exception as e:
            print(f"Error during question handling for {client.username}: {e}")

    def handle_chat(self, client):
        try:
            while True:  # Keep the user in the gaming room
                client.send("Choose chat type: 1. Public, 2. Private, 0. Back")
                chat_type = int(client.socket.recv(1024).decode().strip())
                if chat_type == 1:
                    client.send("Enter your public message:")
                    msg = client.socket.recv(1024).decode().strip()
                    client.game_room.store_message(f"{client.username} (public): {msg}")  # Store public message in room
                    client.game_room.broadcast(f"{client.username} (public): {msg}", client)  # Broadcast to clients in room
                elif chat_type == 2:
                    client.send("Enter the recipient's username:")
                    recipient_name = client.socket.recv(1024).decode().strip()
                    recipient = next((c for c in client.game_room.clients if c.username == recipient_name), None)
                    if recipient:
                        client.send("Enter your private message:")
                        msg = client.socket.recv(1024).decode().strip()
                        recipient.send(f"{client.username} (private): {msg}")  # Send private message to recipient
                    else:
                        client.send("Recipient not found in the room.")
                elif chat_type == 3:
                    break  # Go back to previous menu
        except Exception as e:
            print(f"Error during chat handling for {client.username}: {e}")

    def leave_room(self, client):
        if client.game_room:
            client.game_room.remove_client(client)
            client.send("You have left the game room.")
            client.game_room = None

if __name__ == "__main__":
    server = Server('127.0.0.1', 65432)
    server.start()