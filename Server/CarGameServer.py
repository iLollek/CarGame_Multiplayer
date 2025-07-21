import socket
import threading
import json

class LogLevel:
    INFO = 'INFO'
    WARN = 'WARN'
    ERROR = 'ERROR'

class ClientHandler(threading.Thread):
    """Handles a single client connection."""

    def __init__(self, conn, addr, server):
        super().__init__(daemon=True)
        self.conn = conn
        self.addr = addr
        self.server: CarGameServer = server
        self.running = True
        self.name = None

    def run(self):
        buffer = ""
        self.server.forward_to_ui({"event": "join", "ip_addr": {self.addr[0]}})
        try:
            while self.running:
                data = self.conn.recv(1024)
                if not data:
                    break

                buffer += data.decode('utf-8')

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if not line.strip():
                        continue

                    try:
                        message = json.loads(line)
                        self.name = message.get("name", "Unknown")
                        self.server.broadcast(message, exclude=self)
                        self.server.forward_to_ui(message)
                    except json.JSONDecodeError:
                        print(f"[WARN] Invalid data from {self.addr}: {line}")
        except (ConnectionResetError, ConnectionAbortedError):
            pass
        finally:
            self.stop()

    def send(self, message_dict):
        try:
            data = json.dumps(message_dict) + '\n'
            self.conn.sendall(data.encode('utf-8'))
        except Exception:
            self.stop()

    def stop(self):
        if self.running:
            print(f"[INFO] Client disconnected: {self.addr}")
            self.server.forward_to_ui({"event": "leave", "name": self.name})
            self.running = False
            self.conn.close()
            self.server.remove_client(self)
            self.server.broadcast({"event": "disconnect", "name": f"{self.name}"}, exclude=self)


class CarGameServer:
    """TCP server for multiplayer car game."""

    def __init__(self, host="0.0.0.0", port=5000, ui_callback=None, ui_logbox_callback=None):
        self.host = host
        self.port = port
        self.server_socket = None
        self.clients = []
        self.lock = threading.Lock()
        self.ui_callback = ui_callback  # <--- neu
        self.ui_logbox_callback = ui_logbox_callback

    def start(self):
        """Starts the server and accepts new clients."""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"[INFO] Server started on {self.host}:{self.port}")

        try:
            while True:
                conn, addr = self.server_socket.accept()
                print(f"[INFO] New connection from {addr}")
                handler = ClientHandler(conn, addr, self)
                with self.lock:
                    self.clients.append(handler)
                handler.start()
        except KeyboardInterrupt:
            print("[INFO] Server shutting down...")
        finally:
            self.stop()

    def broadcast(self, message: bytes, exclude=None):
        """Sends a message to all clients except the excluded one."""
        with self.lock:
            for client in self.clients[:]:
                if client != exclude and client.running:
                    client.send(message)

    def remove_client(self, client):
        """Removes a client from the list."""
        with self.lock:
            if client in self.clients:
                self.clients.remove(client)

    def stop(self):
        """Stops the server and all clients."""
        with self.lock:
            for client in self.clients:
                client.stop()
            self.clients.clear()
        if self.server_socket:
            self.server_socket.close()
            print("[INFO] Server socket closed")

    def forward_to_ui(self, message: dict):
        """Optional: Forward message to UI"""
        if self.ui_callback:
            self.ui_callback(message)

    def kick_player_by_name(self, player_name: str, reason: str) -> bool:
        """Kicks a Player from the Server"""
        print(f'Kicking {player_name}')
        try:
            for client in self.clients:
                print(f'Client: {client} - Clients: {self.clients}')
                client: ClientHandler
                if client.name == player_name:
                    # Client found, execute a kick
                    client.send({"event": "kicked", "reason": reason})
                    self.remove_client(client)
                    client.stop()
                    self.ui_logbox_callback(LogLevel.INFO, f'Kicked {player_name} from the Server!')
                    return
            self.ui_logbox_callback(LogLevel.WARN, f'Unable to find {player_name}: Did the Player already disconnect?')
        except Exception as e:
            self.ui_logbox_callback(LogLevel.ERROR, f'Unable to kick {player_name}: {e}')



if __name__ == "__main__":
    server = CarGameServer(host="127.0.0.1", port=5000)
    server.start()
