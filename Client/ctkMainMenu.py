import customtkinter as ctk
from CTkColorPicker import AskColor


class MainMenu:

    def __init__(self):
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.master = ctk.CTk()
        self.master.title("Car Game - Main Menu")
        self.master.geometry("400x400")

        self.result = None
        self.selected_color = "#7800f0"  # Default Hexfarbe

        # Eingabefelder
        self.name_entry = ctk.CTkEntry(master=self.master, placeholder_text="Player Name")
        self.name_entry.pack(pady=10)

        self.server_entry = ctk.CTkEntry(master=self.master, placeholder_text="Server (Example: 127.0.0.1)")
        self.server_entry.insert(0, "127.0.0.1")
        self.server_entry.pack(pady=10)

        self.port_entry = ctk.CTkEntry(master=self.master, placeholder_text="Port (Example: 5000)")
        self.port_entry.insert(0, "5000")
        self.port_entry.pack(pady=10)

        # Farbauswahl
        self.color_button = ctk.CTkButton(master=self.master, text="Choose Car Color", command=self.ask_color)
        self.color_button.pack(pady=10)

        # Fullscreen
        self.fullscreen_checkbox = ctk.CTkCheckBox(master=self.master, text="Fullscreen")
        self.fullscreen_checkbox.pack(pady=10)

        # Start-Button
        self.start_button = ctk.CTkButton(master=self.master, text="Start Game", command=self.on_start)
        self.start_button.pack(pady=20)

        self.master.mainloop()

    def ask_color(self):
        color_picker = AskColor()
        color = color_picker.get()
        if color:
            self.selected_color = color
            self.color_button.configure(fg_color=color)

    def on_start(self):
        self.result = {
            "player_name": self.name_entry.get(),
            "server": self.server_entry.get(),
            "port": int(self.port_entry.get()),
            "car_color": self.hex_to_rgb(self.selected_color),
            "fullscreen": self.fullscreen_checkbox.get()
        }
        self.master.destroy()

    def hex_to_rgb(self, hex_color):
        """Konvertiert eine Hexfarbe (#rrggbb) zu [r, g, b]"""
        hex_color = hex_color.lstrip("#")
        return [int(hex_color[i:i+2], 16) for i in (0, 2, 4)]

    def run(self):
        return self.result
