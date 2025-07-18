import socket
import threading
import json


class CarGameClient:
    """Client for connecting to the car game server."""

    def __init__(self, server_ip, server_port, player_name, car_color: list[int]):
        self.server_ip = server_ip
        self.server_port = server_port
        self.player_name = player_name
        self.sock = None
        self.running = False
        self.receive_thread = None
        self.car_color = car_color

        self.other_players = {}
        self.on_player_update = None
        self.on_player_disconnect = None

    def connect(self):
        """Establish connection to the server and start listening thread."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.server_ip, self.server_port))
        self.running = True
        self.receive_thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.receive_thread.start()
        print(f"[INFO] Connected to server at {self.server_ip}:{self.server_port}")

    def receive_loop(self):
        """Listen for incoming messages from server."""
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(1024)
                if not data:
                    break

                buffer += data.decode('utf-8')

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line)

                        if "event" in message:
                            self.event_handler(message)
                            continue

                        name = message.get("name")
                        if name == self.player_name:
                            continue

                        self.other_players[name] = message
                        if self.on_player_update:
                            self.on_player_update(name, message)

                    except json.JSONDecodeError:
                        print(f"[WARN] Received invalid JSON: {line}")
            except ConnectionResetError:
                print("[ERROR] Server connection lost (ConnectionResetError)")
                break

        self.running = False

    def send_player_state(self, x, y, angle, is_drifting, car_color):
        """Send the local player's position/state to the server."""
        if not self.running:
            return
        try:
            message = {
                "name": self.player_name,
                "x": x,
                "y": y,
                "angle": angle,
                "is_drifting": is_drifting,
                "car_color": car_color
            }
            # send JSON with newline delimiter
            self.sock.sendall((json.dumps(message) + '\n').encode('utf-8'))
        except Exception as e:
            print(f"[ERROR] Failed to send data: {e}")
            self.running = False

    def event_handler(self, message: dict):
        print(f'[INFO] Received Event: {message["event"]}')
        event = message.get("event")

        if event == "disconnect":
            self.on_player_disconnect(message.get("name"))

    def close(self):
        """Close the connection to the server."""
        self.running = False
        if self.sock:
            self.sock.close()
            print("[INFO] Disconnected from server")
