import os
import time
import socket
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import threading
from flask import Flask, jsonify, request

# GPIO setup using gpiozero
from gpiozero import LED, InputDevice

SLOT_PINS = {
    "Slot1": 17,
    "Slot2": 18,
    "Slot3": 27,
    "Slot4": 22
}

SENSORS = {slot: InputDevice(pin, pull_up=True) for slot, pin in SLOT_PINS.items()}

SSID = "Aarav1"
PASSWORD = "117@pranav"

# Flask app setup
app = Flask(__name__)
data = {
    "Slot1": False,
    "Slot2": False,
    "Slot3": False,
    "Slot4": False
}

def read_sensors():
    for slot, sensor in SENSORS.items():
        data[slot] = sensor.value == 1  # HIGH = Occupied

@app.route('/data', methods=['GET'])
def get_data():
    read_sensors()
    return jsonify(data)

@app.route('/update', methods=['POST'])
def update_data():
    try:
        new_data = request.get_json()
        if not new_data:
            return jsonify({"status": "error", "message": "No JSON data received"}), 400

        for key in new_data:
            if key in data:
                data[key] = new_data[key]

        return jsonify({"status": "success", "updated": new_data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

def connect_to_wifi(ssid, password):
    wifi_conf = f'''
network={{
    ssid="{ssid}"
    psk="{password}"
}}
'''
    with open("/etc/wpa_supplicant/wpa_supplicant.conf", "a") as f:
        f.write(wifi_conf)

    os.system("sudo wpa_cli -i wlan0 reconfigure")
    time.sleep(10)

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except:
        ip = "Unavailable"
    finally:
        s.close()
    return ip

def show_parking_gui():
    import requests
    root = tk.Tk()
    root.title("Parking GUI")
    root.overrideredirect(True)
    root.attributes("-fullscreen", True)
    root.wm_attributes("-topmost", 1)
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.configure(bg="#ffdb4d")

    def on_exit():
        root.destroy()

    title = tk.Label(root, text="Smart Parking", font=("Helvetica", 40, "bold"), bg="#ffdb4d", fg="#333")
    title.pack(pady=40)

    slot_frame = tk.Frame(root, bg="#ffdb4d")
    slot_frame.pack(pady=20)

    slot_widgets = {}
    last_data = {}

    for i in range(4):
        row, col = divmod(i, 2)
        slot = tk.Frame(slot_frame, bg="#4CAF50", bd=2, relief="ridge", width=300, height=220)
        slot.grid(row=row, column=col, padx=35, pady=35)
        slot.grid_propagate(False)

        label_title = tk.Label(slot, text=f"Slot {i+1}", font=("Helvetica", 24, "bold"), bg="#4CAF50", fg="white")
        label_status = tk.Label(slot, text="Available", font=("Helvetica", 20), bg="#4CAF50", fg="white")
        label_title.pack(pady=20)
        label_status.pack()

        slot_widgets[f"Slot{i+1}"] = (slot, label_title, label_status)
        last_data[f"Slot{i+1}"] = None

    def update_slots():
        nonlocal last_data
        try:
            response = requests.get("http://localhost/data", timeout=2)
            slot_data = response.json()

            for i in range(4):
                key = f"Slot{i+1}"
                occupied = slot_data.get(key, False)
                if last_data[key] != occupied:
                    color = "#F44336" if occupied else "#4CAF50"
                    status_text = "Occupied" if occupied else "Available"

                    slot, title, status = slot_widgets[key]
                    slot.configure(bg=color)
                    title.configure(bg=color)
                    status.configure(bg=color, text=status_text)

                    last_data[key] = occupied
        except Exception as e:
            print(f"Failed to update slots: {e}")

        root.after(5000, update_slots)

    update_slots()

    exit_btn = tk.Button(root, text="Exit", command=on_exit, font=("Helvetica", 16), bg="red", fg="white")
    exit_btn.place(x=screen_width - 10, y=10, anchor="ne")

    root.mainloop()

def show_ip_screen(ip):
    root = tk.Tk()
    root.title("Connected")
    root.overrideredirect(True)
    root.attributes("-fullscreen", True)
    root.wm_attributes("-topmost", 1)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.configure(bg="#ffdb4d")

    PORT = 80

    def on_exit():
        root.destroy()

    def on_next():
        root.destroy()
        show_parking_gui()

    frame = tk.Frame(root, bg="#ffdb4d")
    frame.place(relx=0.5, rely=0.5, anchor='center')

    tk.Label(frame, text=f"Connected!\nIP Address: {ip}:{PORT}", font=("Helvetica", 32, "bold"), bg="#ffdb4d").pack(pady=100)

    next_btn = tk.Button(frame, text="Next", command=on_next, font=("Helvetica", 20), bg="#33c4ff", fg="white")
    next_btn.pack(pady=20)

    exit_btn = tk.Button(root, text="Exit", command=on_exit, font=("Helvetica", 16), bg="red", fg="white")
    exit_btn.place(x=screen_width - 10, y=10, anchor="ne")

    root.mainloop()

def show_wifi_gui():
    root = tk.Tk()
    root.title("Wi-Fi Setup")
    root.overrideredirect(True)
    root.attributes("-fullscreen", True)
    root.wm_attributes("-topmost", 1)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}+0+0")
    root.configure(bg="#ffdb4d")

    def on_connect():
        ssid = ssid_entry.get()
        password = password_entry.get()
        if ssid and password:
            connect_to_wifi(ssid, password)
            root.destroy()
            ip = get_ip_address()
            threading.Thread(target=lambda: app.run(host='0.0.0.0', port=80)).start()
            show_ip_screen(ip)

    def on_exit():
        root.destroy()

    frame = tk.Frame(root, bg="#ffdb4d")
    frame.place(relx=0.5, rely=0.5, anchor='center')

    try:
        logo_img = Image.open("Valet Droid.png")
        logo_img = logo_img.resize((100, 100), Image.LANCZOS)
        logo = ImageTk.PhotoImage(logo_img)
        logo_label = tk.Label(root, image=logo, bg="#ffdb4d")
        logo_label.image = logo
        logo_label.place(relx=0.02, rely=0.03, anchor='nw')
    except:
        pass

    tk.Label(frame, text="SSID:", font=("Helvetica", 24), bg="#ffdb4d").grid(row=0, column=0, pady=10)
    ssid_entry = tk.Entry(frame, font=("Helvetica", 24), width=25, bg="white")
    ssid_entry.grid(row=0, column=1, pady=10)

    tk.Label(frame, text="Password:", font=("Helvetica", 24), bg="#ffdb4d").grid(row=1, column=0, pady=10)
    password_entry = tk.Entry(frame, font=("Helvetica", 24), show='*', width=25, bg="white")
    password_entry.grid(row=1, column=1, pady=10)

    connect_btn = tk.Button(frame, text="Connect", font=("Helvetica", 20), bg="#33c4ff", command=on_connect)
    connect_btn.grid(row=2, column=0, columnspan=2, pady=40)

    exit_btn = tk.Button(root, text="Exit", command=on_exit, font=("Helvetica", 16), bg="red", fg="white")
    exit_btn.place(x=screen_width - 10, y=10, anchor="ne")

    root.mainloop()

if __name__ == '__main__':
    show_wifi_gui()
