import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

class LogLevel:
    INFO = 'INFO'
    WARN = 'WARN'
    ERROR = 'ERROR'


class CarGameServerUI(tk.Tk):
    """
    Graphische Benutzeroberfläche zur Anzeige und Verwaltung verbundener Spieler.
    """

    def __init__(self):
        super().__init__()
        self.title("Car Game Server UI")
        self.geometry("1000x600")
        self.players = {}
        self._build_ui()
        self.player_kick_by_name_function = None

    def _build_ui(self):
        # Spieler-Tabelle
        columns = (
            "Name", "Color", "Points", "Speed", "Drifting",
            "Boosting", "X", "Y", "Angle"
        )
        self.player_tree = ttk.Treeview(self, columns=columns, show='headings')

        for col in columns:
            self.player_tree.heading(col, text=col)
            self.player_tree.column(col, stretch=True, anchor="center")

        self.player_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Kick Button
        kick_btn = ttk.Button(self, text="Kick Selected Player", command=self.kick_selected_player)
        kick_btn.pack(pady=5)

        # Statistikbereich
        self.stats_label = tk.Label(self, text="Stats: ", anchor="w", justify="left")
        self.stats_label.pack(fill=tk.X, padx=10)

        # Logbox
        self.log_box = ScrolledText(self, height=10, state="disabled", bg="black", fg="white")
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def update_player(self, player_data):
        """
        Aktualisiert oder fügt einen Spieler in der Tabelle hinzu.

        :param player_data: dict mit allen Feldern vom Client
        """
        name = player_data["name"]
        self.players[name] = player_data

        # Gibt es den Spieler bereits?
        existing_items = self.player_tree.get_children()
        found = False
        for item in existing_items:
            values = self.player_tree.item(item, 'values')
            if values and values[0] == name:
                self.player_tree.item(item, values=self._player_to_row(player_data))
                found = True
                break

        if not found:
            self.player_tree.insert('', tk.END, values=self._player_to_row(player_data))

        # self.log(LogLevel.INFO, f"Update from {name}")
        self.update_stats()

    def remove_player(self, name):
        """
        Entfernt einen Spieler aus der UI.

        :param name: Spielername
        """
        self.players.pop(name, None)
        for item in self.player_tree.get_children():
            values = self.player_tree.item(item, 'values')
            if values and values[0] == name:
                self.player_tree.delete(item)
                break
        self.update_stats()
        self.log(LogLevel.INFO, f"Player '{name}' removed")

    def kick_selected_player(self):
        """
        Entfernt den aktuell ausgewählten Spieler aus der UI.
        (Erweiterbar: Kommunikation mit dem Server über Queue oder Socket)
        """
        selected = self.player_tree.selection()
        if not selected:
            return

        item = selected[0]
        name = self.player_tree.item(item)['values'][0]
        self.remove_player(name)
        self.log(LogLevel.WARN, f"Player '{name}' kicked (local only)")

    def update_stats(self):
        """
        Berechnet und zeigt einfache Statistiken an.
        """
        total = len(self.players)
        avg_speed = 0
        if total > 0:
            avg_speed = sum(p.get("speed_kmh", 0) for p in self.players.values()) / total
        self.stats_label.config(text=f"Stats: Players = {total}, Avg Speed = {avg_speed:.1f} km/h")

    def log(self, level, message):
        """
        Fügt eine Nachricht in das Log-Feld ein mit Farbanpassung.

        :param level: INFO | WARN | ERROR
        :param message: Lognachricht
        """
        self.log_box.config(state='normal')
        color = {"INFO": "white", "WARN": "yellow", "ERROR": "red"}.get(level, "white")
        self.log_box.insert(tk.END, f"[{level}] {message}\n", level)
        self.log_box.tag_config(level, foreground=color)
        self.log_box.config(state='disabled')
        self.log_box.see(tk.END)

    def _player_to_row(self, player):
        """
        Konvertiert ein Spielerobjekt in eine Darstellungszeile für das TreeView.

        :param player: dict mit Spielerinformationen
        :return: Tupel mit Werten für das TreeView
        """
        return (
            player.get("name", ""),
            player.get("car_color", ""),
            player.get("points", 0),
            player.get("speed_kmh", 0),
            "Yes" if player.get("is_drifting") else "No",
            "Yes" if player.get("is_boosting") else "No",
            round(player.get("x", 0), 1),
            round(player.get("y", 0), 1),
            round(player.get("angle", 0), 1)
        )
