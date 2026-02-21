#!/usr/bin/env python3
import os
import sys
import socket
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from smb.SMBConnection import SMBConnection
from cryptography.fernet import Fernet
from PIL import Image, ImageTk
import requests


# ---------------- CONFIG ---------------- #
INFO_URL = "http://chronos.local/info"
CRED_FILE = "cred.dat"
KEY_FILE = "key.key"
SHARE_NAME = "shared"

# ---------------- ENCRYPTION ---------------- #
def load_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
    return open(KEY_FILE, "rb").read()

fernet = Fernet(load_key())

def save_username(username):
    encrypted = fernet.encrypt(username.encode())
    with open(CRED_FILE, "wb") as f:
        f.write(encrypted)

def load_username():
    if not os.path.exists(CRED_FILE):
        return ""
    try:
        with open(CRED_FILE, "rb") as f:
            return fernet.decrypt(f.read()).decode()
    except:
        return ""

# ---------------- MAIN APP ---------------- #
class ChronosApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Chronos Control Panel V10")
        self.geometry("800x600")
        self.resizable(True, True)

        self.server_ip = None
        self.server_name = "Loading..."
        self.version = "Loading..."
        self.status_online = False
        self.smb_conn = None
        self.username = None
        self.password = None

        # --- HEADER --- #
        tk.Label(self, text="CHRONOS CONTROL PANEL", font=("Arial", 20, "bold")).pack(pady=10)

        # --- Status LED --- #
        self.status_label = tk.Label(self, text="OFFLINE", fg="red", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=5)

        # --- Info Frame --- #
        self.info_frame = tk.Frame(self, bg="#2b2b2b")
        self.info_frame.pack(padx=15, pady=5, fill="x")
        self.name_label = tk.Label(self.info_frame, text=f"Server: {self.server_name}", bg="#2b2b2b", fg="white")
        self.name_label.pack(anchor="w", padx=15, pady=2)
        self.ip_label = tk.Label(self.info_frame, text=f"IP: {self.server_ip}", bg="#2b2b2b", fg="white")
        self.ip_label.pack(anchor="w", padx=15, pady=2)
        self.version_label = tk.Label(self.info_frame, text=f"Version: {self.version}", bg="#2b2b2b", fg="white")
        self.version_label.pack(anchor="w", padx=15, pady=2)

        # --- Buttons --- #
        self.button_frame = tk.Frame(self, bg="#2b2b2b")
        self.button_frame.pack(padx=15, pady=5, fill="x")

        tk.Button(self.button_frame, text="Refresh Info", command=self.get_info).pack(pady=5, padx=15, fill="x")
        tk.Button(self.button_frame, text="Connect to SMB", command=self.show_login).pack(pady=5, padx=15, fill="x")

        # SSH Terminal Button
        tk.Button(self.button_frame, text="Open SSH Terminal", bg="#3498db",
                  command=self.open_ssh_terminal).pack(pady=5, padx=15, fill="x")
                  
                  
        # --- File Explorer Treeview --- #
        self.tree_frame = tk.Frame(self, bg="#2b2b2b")
        self.tree_frame.pack(padx=15, pady=10, fill="both", expand=True)
        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.pack(fill="both", expand=True, side="left")
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)

        self.scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)



        # --- INIT --- #
        self.get_info()
        self.after(1000, self.update_status)

    # ---------------- SERVER INFO ---------------- #
    def get_info(self):
        def fetch():
            try:
                resp = requests.get(INFO_URL, timeout=3).json()
                self.server_ip = resp.get("server ip")
                self.server_name = resp.get("name", "Unknown")
                self.version = resp.get("version", "Unknown")
            except:
                self.server_ip = None
                self.server_name = "N/A"
                self.version = "N/A"
            self.update_labels()
        threading.Thread(target=fetch, daemon=True).start()

    def update_labels(self):
        self.name_label.configure(text=f"Server: {self.server_name}")
        self.ip_label.configure(text=f"IP: {self.server_ip}")
        self.version_label.configure(text=f"Version: {self.version}")

    # ---------------- STATUS LED ---------------- #
    def update_status(self):
        if self.server_ip:
            def check():
                try:
                    socket.create_connection((self.server_ip, 80), timeout=0.8)
                    online = True
                except:
                    online = False
                self.update_status_led(online)
            threading.Thread(target=check, daemon=True).start()
        else:
            self.update_status_led(False)
        self.after(1000, self.update_status)

    def update_status_led(self, online):
        if online != self.status_online:
            self.status_online = online
            self.status_label.configure(text="ONLINE" if online else "OFFLINE",
                                        fg="lime" if online else "red")

    # ---------------- LOGIN POPUP ---------------- #
    def show_login(self):
        if not self.server_ip:
            messagebox.showerror("Error", "Server IP not loaded.")
            return

        login = tk.Toplevel(self)
        login.geometry("320x220")
        login.title("SMB Login")
        login.grab_set()

        tk.Label(login, text="Username").pack(pady=5)
        username_entry = tk.Entry(login)
        username_entry.pack()
        username_entry.insert(0, load_username())

        tk.Label(login, text="Password").pack(pady=5)
        password_entry = tk.Entry(login, show="*")
        password_entry.pack()

        remember_var = tk.BooleanVar()
        tk.Checkbutton(login, text="Remember Username", variable=remember_var).pack(pady=10)

        def connect():
            self.username = username_entry.get()
            self.password = password_entry.get()
            if remember_var.get():
                save_username(self.username)
            login.destroy()
            threading.Thread(target=self.connect_smb, daemon=True).start()

        tk.Button(login, text="Connect", command=connect).pack(pady=10)

    # ---------------- SMB CONNECT ---------------- #
    def connect_smb(self):
        if not self.server_ip:
            return
        try:
            self.smb_conn = SMBConnection(self.username, self.password,
                                          "ChronosClient", self.server_name, use_ntlm_v2=True)
            connected = self.smb_conn.connect(self.server_ip, 139, timeout=5)
            if connected:
                self.load_tree("")
                messagebox.showinfo("Connected", "Connected to SMB share!")
            else:
                messagebox.showerror("SMB Error", "Failed to connect to SMB share.")
        except Exception as e:
            messagebox.showerror("SMB Error", str(e))

    # ---------------- TREEVIEW ---------------- #
    def load_tree(self, path, parent=""):
        try:
            items = self.smb_conn.listPath(SHARE_NAME, path if path else "/")
            self.tree.delete(*self.tree.get_children(parent))
            for item in items:
                if item.filename in [".", ".."]:
                    continue
                iid = f"{parent}/{item.filename}" if parent else item.filename
                self.tree.insert(parent, "end", iid=iid, text=item.filename, values=("folder" if item.isDirectory else "file"))
        except Exception as e:
            print("Error loading tree:", e)

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        item_id = selected[0]
        values = self.tree.item(item_id, "values")
        if values[0] == "folder":
            self.load_tree(item_id, parent=item_id)
        else:
            self.open_file(item_id)



    # ---------------- RIGHT-CLICK MENU ---------------- #
    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            item = ""

        self.tree.selection_set(item)

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Upload File", command=lambda: self.upload_file(item))
        menu.add_command(label="Create Folder", command=lambda: self.create_folder(item))

        if item != "":
            menu.add_command(label="Delete", command=lambda: self.delete_item(item))

        menu.post(event.x_root, event.y_root)
        
    # ---------------- CREATE FOLDER ---------------- #
    def create_folder(self, item_id):
        folder_name = simpledialog.askstring("New Folder", "Enter folder name:")
        if not folder_name:
            return

        if item_id == "":
            path = f"/{folder_name}"
            parent = ""
        else:
            values = self.tree.item(item_id, "values")
            if values[0] == "folder":
                path = f"/{item_id}/{folder_name}"
                parent = item_id
            else:
                parent_dir = os.path.dirname(item_id)
                path = f"/{parent_dir}/{folder_name}" if parent_dir else f"/{folder_name}"
                parent = parent_dir

        try:
            self.smb_conn.createDirectory(SHARE_NAME, path)
            messagebox.showinfo("Success", "Folder created successfully.")
            self.load_tree(parent, parent=parent)
        except Exception as e:
            messagebox.showerror("Create Folder Error", str(e))

    # ---------------- UPLOAD FILE ---------------- #
    def upload_file(self, item_id):
        # Ask user to select one or more files
        filepaths = filedialog.askopenfilenames(title="Select files to upload")
        if not filepaths:
            return

        # Determine destination folder
        if item_id == "":
            dest_path = "/"
        else:
            values = self.tree.item(item_id, "values")
            if values[0] == "folder":
                dest_path = f"/{item_id}"
            else:
                dest_path = f"/{os.path.dirname(item_id)}" if "/" in item_id else "/"

        for filepath in filepaths:
            try:
                with open(filepath, "rb") as f:
                    filename = os.path.basename(filepath)
                    self.smb_conn.storeFile(SHARE_NAME, f"{dest_path}/{filename}", f)
                messagebox.showinfo("Success", f"{filename} uploaded!")
            except Exception as e:
                messagebox.showerror("Upload Error", str(e))

        # Reload tree
        parent = dest_path.strip("/") or ""
        self.load_tree(dest_path, parent=parent)

    # ---------------- DELETE ITEM ---------------- #
    def delete_item(self, item_id):
        if not messagebox.askyesno("Confirm Delete", f"Delete {item_id}?"):
            return

        values = self.tree.item(item_id, "values")

        try:
            if values[0] == "folder":
                self.delete_folder_recursive(f"/{item_id}")
            else:
                self.smb_conn.deleteFiles(SHARE_NAME, f"/{item_id}")

            messagebox.showinfo("Deleted", f"{item_id} deleted!")

            parent = os.path.dirname(item_id) if "/" in item_id else ""
            self.load_tree(parent, parent=parent)

        except Exception as e:
            messagebox.showerror("Delete Error", str(e))
            
    def delete_folder_recursive(self, path):
        items = self.smb_conn.listPath(SHARE_NAME, path)

        for item in items:
            if item.filename in [".", ".."]:
                continue

            full_path = f"{path}/{item.filename}"

            if item.isDirectory:
                self.delete_folder_recursive(full_path)
            else:
                self.smb_conn.deleteFiles(SHARE_NAME, full_path)

        self.smb_conn.deleteDirectory(SHARE_NAME, path)

    # ---------------- OPEN FILE ---------------- #
    def open_file(self, path):
        local_path = os.path.join(os.path.expanduser("~"), os.path.basename(path))
        try:
            with open(local_path, "wb") as f:
                self.smb_conn.retrieveFile(SHARE_NAME, f"/{path}", f)
            if sys.platform.startswith("win"):
                os.startfile(local_path)
            elif sys.platform.startswith("linux"):
                subprocess.Popen(["xdg-open", local_path])
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", local_path])
        except Exception as e:
            messagebox.showerror("Open File Error", str(e))
            
    def open_ssh_terminal(self):
        import json

        # Step 1: Fetch server info
        try:
            resp = requests.get(INFO_URL, timeout=3).json()
            server_ip = resp.get("server ip")
            server_psw = resp.get("server psw")
            default_psw = resp.get("server psw default", "false").lower() == "true"
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch server info:\n{e}")
            return

        if not server_ip:
            messagebox.showerror("Error", "Server IP not available.")
            return

        # Step 2: Build SSH command
        ssh_command = f"ssh chronos@{server_ip}"

        # Step 3: If default password, try to auto-insert
        if default_psw and server_psw:
            if sys.platform.startswith("linux") or sys.platform.startswith("darwin"):
                # Use sshpass on Linux/macOS
                ssh_command = f'sshpass -p "{server_psw}" ssh chronos@{server_ip}'
            elif sys.platform.startswith("win"):
                # Windows: inform user to enter password manually
                messagebox.showinfo("Notice", "Default password detected. Enter password in terminal manually.")
            else:
                messagebox.showerror("Error", f"Unsupported OS: {sys.platform}")
                return

        # Step 4: Open terminal window
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["start", "powershell", "-NoExit", "-Command", ssh_command], shell=True)
            elif sys.platform.startswith("linux"):
                subprocess.Popen(["gnome-terminal", "--", "bash", "-c", ssh_command])
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["osascript", "-e",
                                  f'tell application "Terminal" to do script "{ssh_command}"'])
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ---------------- DASHBOARD COMMAND (PASSWORDLESS SSH) ---------------- #
    def run_dashboard_command(self, action):
        if not self.server_ip or not self.username:
            messagebox.showerror("Error", "Connect to SMB first.")
            return

        def run():
            try:
                # Command to run on the server (passwordless sudo required)
                cmd = f"/mnt/sda1/shared/dashboard.sh {action}"

                ssh_command = [
                    "ssh",
                    "-o", "StrictHostKeyChecking=no",
                    f"{self.username}@{self.server_ip}",
                    cmd
                ]

                # Run the SSH command
                result = subprocess.run(ssh_command, capture_output=True, text=True)

                # Update GUI safely from the main thread
                if result.returncode == 0:
                    self.after(0, lambda: messagebox.showinfo(
                        "Success",
                        f"Dashboard '{action}' executed successfully.\n\nOutput:\n{result.stdout.strip()}"
                    ))
                else:
                    self.after(0, lambda: messagebox.showerror(
                        "Error",
                        f"Command failed with code {result.returncode}.\n\nError:\n{result.stderr.strip()}"
                    ))

            except Exception as e:
                self.after(0, lambda: messagebox.showerror("SSH Error", str(e)))

        threading.Thread(target=run, daemon=True).start()

    # ---------------- DRAG AND DROP ---------------- #
    def on_drop(self, event):
        # event.data contains file paths; we assume a single file for simplicity
        try:
            file_path = event.data.strip("{}")  # Tkinter dnd may wrap paths in {}
            item_id = self.tree.selection()[0] if self.tree.selection() else ""
            self.upload_file(item_id)
        except Exception as e:
            print("Drop upload error:", e)

if __name__ == "__main__":
    app = ChronosApp()
    app.mainloop()