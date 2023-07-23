import os
import time
import argparse
import tkinter as tk
from tkinter import ttk
import threading


def adjust_font_size(event, text_widget):
    # Adjust font size when scrolling mouse wheel while holding the control key
    if event.state & 0x4:
        # if event.delta > 0:
        #     font_size = font_size + 1
        # elif event.delta < 0:
        #     font_size = max(1, font_size - 1)
        pass


class LogMonitorApp(tk.Tk):
    def __init__(self, folder_path):
        super().__init__()
        self.title("Log Monitor")
        self.geometry("800x600")

        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            raise ValueError(f"Invalid path: '{folder_path}' does not exist or is not a directory.")

        self.count = 0
        self.folder_path = folder_path
        self.file_positions = {}  # Dictionary to store the last known file positions
        self.file_tab_ids = {}  # Dictionary to store the tab IDs
        self.file_text_widgets = {}  # Dictionary to store the text widgets

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill=tk.BOTH)

        self.menu_bar = tk.Menu(self)
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Files", menu=self.file_menu)
        self.config(menu=self.menu_bar)

        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_change)

        # Start monitor thread
        self.monitor_thread = threading.Thread(target=self.monitor_folder)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def monitor_folder(self):
        while True:
            self.count += 1
            file_list = os.listdir(self.folder_path)

            # Sort file list alphabetically
            file_list.sort()

#            print(f'count = {self.count}, file_list = {file_list}')

            # Check for new files
            for filename in file_list:
                if filename.endswith(".log"):
                    if filename not in self.file_positions:
                        print(f'New - filename = {filename}')
                        self.file_positions[filename] = 0
                        tab = ttk.Frame(self.notebook)
                        self.notebook.add(tab, text=filename)
                        text_widget = tk.Text(tab)
                        text_widget.pack(expand=True, fill=tk.BOTH)
                        text_widget.bind("<Control-MouseWheel>",
                                         lambda event,
                                         widget=text_widget: adjust_font_size(event, widget))
                        self.file_text_widgets[filename] = text_widget
                        self.file_tab_ids[filename] = self.get_file_tab_id(filename)

                        # Add vertical scrollbar
                        y_scrollbar = tk.Scrollbar(tab, command=text_widget.yview)
                        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                        text_widget.config(yscrollcommand=y_scrollbar.set)

                        # Add horizontal scrollbar
                        x_scrollbar = tk.Scrollbar(tab, command=text_widget.xview, orient=tk.HORIZONTAL)
                        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
                        text_widget.config(xscrollcommand=x_scrollbar.set)

                        # Update the menu with new file
                        self.file_menu.add_command(label=filename,
                                                   command=lambda file=filename: self.show_file_tab(file))

                    self.update_display(filename)

            # Check for removed files
            for filename in list(self.file_positions):
                if filename not in file_list:
                    self.notebook.forget(self.file_tab_ids[filename])
                    self.file_menu.delete(filename)
                    del self.file_positions[filename]
                    del self.file_text_widgets[filename]
                    del self.file_tab_ids[filename]

            time.sleep(1)  # Adjust the interval for checking updates

    def update_display(self, filename):
        try:
            with open(os.path.join(self.folder_path, filename), "r") as file:
                file.seek(self.file_positions[filename])
                new_content = file.read()
                if new_content:
                    text_widget = self.file_text_widgets[filename]
                    text_widget.insert(tk.END, new_content)
                    self.file_positions[filename] = file.tell()

                    # Add asterisk to the beginning of the tab name
                    tab_id = self.file_tab_ids[filename]
                    tab_text = self.notebook.tab(tab_id, "text")
                    if not tab_text.startswith("*"):
                        self.notebook.tab(tab_id, text="*" + tab_text)

        except FileNotFoundError as ex:
            print(f"File not found: '{filename}'")
            print(f"Exception: {ex}")

    def on_tab_change(self, event):
        # Remove asterisk when the tab is clicked
        current_tab_text = self.notebook.tab(self.notebook.select(), "text")
        if current_tab_text.startswith("*"):
            self.notebook.tab(self.notebook.select(), text=current_tab_text[1:])

    def show_file_tab(self, filename):
        tab_id = self.get_file_tab_id(filename)
        if tab_id is not None:
            self.notebook.select(tab_id)

    def get_file_tab_id(self, filename):
        for tab_id in self.notebook.tabs():
            if self.notebook.tab(tab_id, "text") == filename:
                return tab_id
        return None


if __name__ == "__main__":
    dir_path = os.path.dirname(os.path.realpath(__file__))
    print(f'dir_path = {dir_path}')

    cwd = os.getcwd()
    print(f'cwd = {cwd}')

    parser = argparse.ArgumentParser(
        description="Log Monitor - Monitor log files in a folder and display them in a GUI.")
    parser.add_argument("--folder_path", help="Path to monitor for log files", default=".")
    args = parser.parse_args()
    print(f'args.folder_path = {args.folder_path}')

    try:
        print(f'Define app')
        app = LogMonitorApp(args.folder_path)
        print(f'START - app.mainloop()')
        app.mainloop()
        print(f'END - app.mainloop()')
    except ValueError as e:
        print(f"Error: {e}")
