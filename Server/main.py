import threading
from CarGameServer import CarGameServer
from ServerGUI import CarGameServerUI  # die angepasste UI-Klasse

def main():
    app = CarGameServerUI()

    def ui_callback(message: dict):
        app.update_player(message)

    def start_server():
        server = CarGameServer(host="127.0.0.1", port=5000, ui_callback=ui_callback)
        server.start()

    threading.Thread(target=start_server, daemon=True).start()
    app.mainloop()

if __name__ == "__main__":
    main()
