import os
import json
import tkinter
import customtkinter
from PIL import Image, ImageTk
import qrcode
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox

# Set working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = "match_data.json"

# Data persistence functions
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

saved_matches = load_data()

# Global variables
selected_color = None
current_match = None
team_number = ""
counters = {"L1": 0, "L2": 0, "L3": 0, "L4": 0,
            "Algae Removed": 0, "Algae Processed": 0, "Algae Netted": 0}
moved_state = "No"
action_history = []
auto_counter_labels = {}
teleop_counters = {"L1": 0, "L2": 0, "L3": 0, "L4": 0,
                   "Algae Removed": 0, "Algae Processed": 0, "Algae Netted": 0}
teleop_history = []
climb_state = "No barge"
teleop_broken_state = "No"
robot_coords = None
MAX_COMMENT_LENGTH = 100
last_data_str = ""

# --- Generic Helper Functions ---

# Updates a counter and its associated UI label(s)
def update_counter(counter_dict, label_dicts, key, delta, history):
    old = counter_dict[key]
    counter_dict[key] += delta
    for labels in label_dicts:
        if key in labels:
            labels[key].configure(text=f"{key}: {counter_dict[key]}")
    history.append(("counter", key, old))

# Generic function for updating the remaining character count
def update_comment_count(comment_box, count_label, event=None):
    text = comment_box.get("1.0", "end-1c")
    remaining = MAX_COMMENT_LENGTH - len(text)
    count_label.configure(text=f"{remaining} characters remaining")

# --- State Reset and QR Code Generation ---

def reset_current_state():
    global team_number, counters, moved_state, teleop_counters, climb_state, teleop_broken_state, robot_coords
    team_number = ""
    counters = {k: 0 for k in counters}
    moved_state = "No"
    teleop_counters = {k: 0 for k in teleop_counters}
    climb_state = "No barge"
    teleop_broken_state = "No"
    robot_coords = None
    # Reset UI elements:
    team_number_entry.configure(state="normal")
    team_number_entry.delete(0, "end")
    red_button.configure(state="normal")
    blue_button.configure(state="normal")
    auto_comment_box.delete("1.0", "end")
    teleop_comment_box.delete("1.0", "end")
    for label in auto_counter_labels.values():
        label.configure(text=f"{label.cget('text').split(':')[0]}: 0")
    for label in teleop_counter_labels.values():
        label.configure(text=f"{label.cget('text').split(':')[0]}: 0")
    for label in teleop_counter_labels_extra.values():
        label.configure(text=f"{label.cget('text').split(':')[0]}: 0")

def generate_qr_codes(data_str):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return [ImageTk.PhotoImage(img)]

def update_last_data_str():
    global team_number, last_data_str
    team_number = team_number_entry.get().strip()
    auto_comment = auto_comment_box.get("1.0", "end-1c")[:MAX_COMMENT_LENGTH]
    teleop_comment = teleop_comment_box.get("1.0", "end-1c")[:MAX_COMMENT_LENGTH]
    data = {
        "match_number": current_match,
        "team_number": team_number,
        "selected_color": selected_color,
        "auto": {"counters": counters, "moved_state": moved_state, "robot_coords": robot_coords, "comment": auto_comment},
        "teleop": {"counters": teleop_counters, "climb_state": climb_state, "teleop_broken_state": teleop_broken_state, "comment": teleop_comment}
    }
    last_data_str = json.dumps(data)

def get_match_data():
    if current_match in saved_matches:
        return json.dumps(saved_matches[current_match])
    else:
        update_last_data_str()
        return last_data_str

def copy_data():
    data_str = get_match_data()
    root.clipboard_clear()
    root.clipboard_append(data_str)
    messagebox.showinfo("Copied", "QR code data copied to clipboard.")

def download_data():
    data_str = get_match_data()
    folder = filedialog.askdirectory(title="Select download folder")
    if folder:
        file_path = os.path.join(folder, f"{team_number}_{current_match}.json")
        with open(file_path, "w") as f:
            f.write(data_str)
        messagebox.showinfo("Downloaded", f"Match data saved to:\n{file_path}")

def update_qr_code_in_container(container):
    update_last_data_str()
    global qr_codes, current_qr_index
    qr_codes = generate_qr_codes(last_data_str)
    current_qr_index = 0
    for widget in container.winfo_children():
        widget.destroy()
    btn_frame = customtkinter.CTkFrame(container)
    btn_frame.pack(pady=5)
    customtkinter.CTkButton(btn_frame, text="Copy Data", command=copy_data).pack(side="left", padx=5)
    customtkinter.CTkButton(btn_frame, text="Download", command=download_data).pack(side="left", padx=5)
    if qr_codes:
        customtkinter.CTkLabel(container, image=qr_codes[current_qr_index], text="").pack(pady=10)

# --- Match Selection and Editing ---

def on_match_select(match):
    reset_current_state()
    global current_match
    current_match = match
    team_frame.pack_forget()
    saved_data_label.pack_forget()
    edit_button.pack_forget()
    if 'qr_container' in globals():
        qr_container.destroy()
    if match in saved_matches:
        display_saved_data(match)
    else:
        team_title_label.configure(text="Select Team")
        team_frame.pack(pady=20)

def display_saved_data(match):
    data = saved_matches[match]
    team_number_entry.configure(state="normal")
    team_number_entry.delete(0, "end")
    team_number_entry.insert(0, data.get("team_number", ""))
    team_number_entry.configure(state="disabled")
    col = data.get("selected_color", "")
    if col:
        select_team_color(col)
        red_button.configure(state="disabled")
        blue_button.configure(state="disabled")
    summary = (f"Saved Data:\nMatch: {match}\nTeam: {data.get('team_number','')}\n"
               f"Alliance: {data.get('selected_color','')}\nAuto: {data.get('auto',{})}\nTeleOp: {data.get('teleop',{})}")
    saved_data_label.configure(text=summary)
    saved_data_label.pack(pady=5)
    edit_button.pack(pady=5)
    team_frame.pack(pady=20)
    global qr_container
    qr_container = customtkinter.CTkFrame(team_frame)
    qr_container.pack(pady=5)
    update_qr_code_in_container(qr_container)

def edit_match_data():
    team_number_entry.configure(state="normal")
    red_button.configure(state="normal")
    blue_button.configure(state="normal")
    saved_data_label.pack_forget()
    edit_button.pack_forget()

def select_team_color(color):
    global selected_color
    selected_color = color
    if color == "Red":
        red_button.configure(fg_color="red")
        blue_button.configure(fg_color="gray")
    else:
        blue_button.configure(fg_color="blue")
        red_button.configure(fg_color="gray")

# --- Match Phases and UI Navigation ---

def start_match():
    global team_number
    team_number = team_number_entry.get().strip()
    field_frame.pack_forget()
    left_frame.pack_forget()
    show_starting_position()

def show_starting_position():
    start_position_frame.pack(fill="both", expand=True)
    draw_starting_canvas()

def draw_starting_canvas():
    global robot_coords, sp_image_tk
    sp_image = sp_img.transpose(Image.FLIP_LEFT_RIGHT) if selected_color == "Blue" else sp_img
    sp_image_tk = ImageTk.PhotoImage(sp_image)
    position_canvas.delete("all")
    position_canvas.create_image(0, 0, anchor="nw", image=sp_image_tk)
    text_color = "red" if selected_color == "Red" else "blue"
    position_canvas.create_text(5, 5, text=f"Team {team_number} - {selected_color}",
                                fill=text_color, font=("Arial", 16, "bold"), anchor="nw")
    rect_size = 40
    robot_rect = position_canvas.create_rectangle(10, 10, 10+rect_size, 10+rect_size,
                                                   fill="red", outline="black")
    robot_coords = position_canvas.coords(robot_rect)
    drag_data = {"x": 0, "y": 0, "item": None}
    def on_button_press(event):
        clicked = position_canvas.find_closest(event.x, event.y)
        if clicked and clicked[0] == robot_rect:
            drag_data["item"] = robot_rect
            drag_data["x"] = event.x
            drag_data["y"] = event.y
    def on_button_release(event):
        drag_data["item"] = None
    def on_motion(event):
        global robot_coords
        if drag_data["item"]:
            x1, y1, x2, y2 = position_canvas.coords(robot_rect)
            dx = event.x - drag_data["x"]
            dy = event.y - drag_data["y"]
            if x1 + dx < 0:
                dx = -x1
            elif x2 + dx > sp_width:
                dx = sp_width - x2
            if y1 + dy < 0:
                dy = -y1
            elif y2 + dy > sp_height:
                dy = sp_height - y2
            position_canvas.move(robot_rect, dx, dy)
            drag_data["x"] = event.x
            drag_data["y"] = event.y
            robot_coords = position_canvas.coords(robot_rect)
    position_canvas.bind("<ButtonPress-1>", on_button_press)
    position_canvas.bind("<ButtonRelease-1>", on_button_release)
    position_canvas.bind("<B1-Motion>", on_motion)

def toggle_moved():
    global moved_state
    old = moved_state
    moved_state = "Yes" if moved_state == "No" else "No"
    moved_button.configure(text=f"Moved away from middle: {moved_state}")
    action_history.append(("toggle", old))

def show_phase3():
    start_position_frame.pack_forget()
    phase3_frame.pack(fill="both", expand=True)

def show_teleop():
    phase3_frame.pack_forget()
    teleop_frame.pack(fill="both", expand=True)

def end_match():
    update_match_data()
    reset_to_match_selection()

def update_match_data():
    auto_comment = auto_comment_box.get("1.0", "end").strip()[:MAX_COMMENT_LENGTH]
    teleop_comment = teleop_comment_box.get("1.0", "end").strip()[:MAX_COMMENT_LENGTH]
    data = {
        "match_number": current_match,
        "team_number": team_number,
        "selected_color": selected_color,
        "auto": {"counters": counters, "moved_state": moved_state, "robot_coords": robot_coords,
                 "climb_state": "N/A", "comment": auto_comment},
        "teleop": {"counters": teleop_counters, "climb_state": climb_state,
                   "teleop_broken_state": teleop_broken_state, "comment": teleop_comment}
    }
    saved_matches[current_match] = data
    save_data(saved_matches)

def reset_to_match_selection():
    global selected_color, current_match, team_number, counters, moved_state, action_history
    global teleop_counters, teleop_history, climb_state, teleop_broken_state, robot_coords
    selected_color = None
    current_match = None
    team_number = ""
    counters = {k: 0 for k in counters}
    moved_state = "No"
    action_history = []
    teleop_counters = {k: 0 for k in teleop_counters}
    teleop_history = []
    climb_state = "No barge"
    teleop_broken_state = "No"
    robot_coords = None
    phase3_frame.pack_forget()
    teleop_frame.pack_forget()
    start_position_frame.pack_forget()
    field_frame.pack(fill="both", expand=True)
    left_frame.pack(side="left", fill="y")

# --- GUI Setup ---

root = customtkinter.CTk()
root.geometry("1200x720")
root.title("Scouting App")
root.configure(bg="light blue")

# Left side: Match selection
left_frame = customtkinter.CTkFrame(root, width=300, height=720)
left_frame.pack(side="left", fill="y")
match_scrollable = customtkinter.CTkScrollableFrame(left_frame, width=280, height=500)
match_scrollable.pack(pady=20, padx=10, fill="both", expand=True)
num_matches = 62
for match in [f"Match {i+1}" for i in range(num_matches)]:
    customtkinter.CTkButton(match_scrollable, text=match,
                            command=lambda m=match: on_match_select(m)).pack(pady=5, padx=10)
saved_data_label = customtkinter.CTkLabel(root, text="", font=("Arial", 14))
edit_button = customtkinter.CTkButton(root, text="Edit", command=edit_match_data, width=150)

# Right side: Main content
right_frame = customtkinter.CTkFrame(root, width=900, height=720)
right_frame.pack(side="right", fill="both", expand=True)
phase_container = customtkinter.CTkFrame(right_frame)
phase_container.pack(fill="both", expand=True)
field_frame = customtkinter.CTkFrame(phase_container)
field_frame.pack(fill="both", expand=True)

# Team selection frame
team_frame = customtkinter.CTkFrame(field_frame)
team_title_label = customtkinter.CTkLabel(team_frame, text="", font=("Arial", 16, "underline"))
team_title_label.pack(pady=10)
team_number_frame = customtkinter.CTkFrame(team_frame)
team_number_frame.pack(pady=5)
customtkinter.CTkLabel(team_number_frame, text="Team Number:").pack(side="left", padx=5)
team_number_entry = customtkinter.CTkEntry(team_number_frame, width=100)
team_number_entry.pack(side="left")
team_button_frame = customtkinter.CTkFrame(team_frame)
team_button_frame.pack(pady=10)
red_button = customtkinter.CTkButton(team_button_frame, text="Red",
                                     command=lambda: select_team_color("Red"), width=100)
red_button.pack(side="left", padx=20)
blue_button = customtkinter.CTkButton(team_button_frame, text="Blue",
                                      command=lambda: select_team_color("Blue"), width=100)
blue_button.pack(side="left", padx=20)
customtkinter.CTkButton(team_frame, text="START", command=start_match, width=150).pack(pady=20)

# Starting position frame
start_position_frame = customtkinter.CTkFrame(phase_container)
sp_img = Image.open("Data/startingPos.jpg")
sp_width, sp_height = sp_img.size
position_canvas = tkinter.Canvas(start_position_frame, width=sp_width, height=sp_height, highlightthickness=0)
position_canvas.pack()
bottom_frame = customtkinter.CTkFrame(start_position_frame)
bottom_frame.pack(pady=10)
customtkinter.CTkButton(bottom_frame, text="START", width=150, command=show_phase3).pack(pady=5)
customtkinter.CTkLabel(bottom_frame, text="Do not start until match starts", font=("Arial", 12)).pack(pady=5)

# Auto Phase (Phase 3) frame
phase3_frame = customtkinter.CTkFrame(phase_container)
l_frame = customtkinter.CTkFrame(phase3_frame)
l_frame.pack(pady=10)
auto_counter_labels = {}
for btn_name in ["L1", "L2", "L3", "L4"]:
    frame = customtkinter.CTkFrame(l_frame)
    frame.pack(side="left", padx=5)
    label = customtkinter.CTkLabel(frame, text=f"{btn_name}: 0", width=60)
    label.pack(side="top")
    customtkinter.CTkButton(frame, text="-", width=30,
                            command=lambda k=btn_name: update_counter(counters, [auto_counter_labels], k, -1, action_history)).pack(side="left")
    customtkinter.CTkButton(frame, text="+", width=30,
                            command=lambda k=btn_name: update_counter(counters, [auto_counter_labels], k, 1, action_history)).pack(side="left")
    auto_counter_labels[btn_name] = label
extra_keys = ["Algae Removed", "Algae Processed", "Algae Netted"]
extra_frame = customtkinter.CTkFrame(phase3_frame)
extra_frame.pack(pady=10)
for key in extra_keys:
    frame = customtkinter.CTkFrame(extra_frame)
    frame.pack(side="left", padx=5)
    label = customtkinter.CTkLabel(frame, text=f"{key}: 0", width=80)
    label.pack(side="top")
    customtkinter.CTkButton(frame, text="-", width=30,
                            command=lambda k=key: update_counter(counters, [auto_counter_labels], k, -1, action_history)).pack(side="left")
    customtkinter.CTkButton(frame, text="+", width=30,
                            command=lambda k=key: update_counter(counters, [auto_counter_labels], k, 1, action_history)).pack(side="left")
    auto_counter_labels[key] = label
moved_button = customtkinter.CTkButton(phase3_frame, text=f"Moved away from middle: {moved_state}",
                                       width=250, command=toggle_moved)
moved_button.pack(pady=10)
auto_comment_box = customtkinter.CTkTextbox(phase3_frame, width=300, height=100, wrap="word")
auto_comment_box.pack(pady=5)
auto_comment_box.bind("<KeyRelease>", lambda event: update_comment_count(auto_comment_box, auto_comment_count_label, event))
auto_comment_count_label = customtkinter.CTkLabel(phase3_frame, text=f"{MAX_COMMENT_LENGTH} characters remaining")
auto_comment_count_label.pack(anchor="e", padx=10)
customtkinter.CTkButton(phase3_frame, text="TeleOp Period", width=150, command=show_teleop).pack(pady=10)

# TeleOp Phase frame
teleop_frame = customtkinter.CTkFrame(phase_container)
teleop_counter_labels = {}
teleop_l_frame = customtkinter.CTkFrame(teleop_frame)
teleop_l_frame.pack(pady=10)
for btn_name in ["L1", "L2", "L3", "L4"]:
    frame = customtkinter.CTkFrame(teleop_l_frame)
    frame.pack(side="left", padx=5)
    label = customtkinter.CTkLabel(frame, text=f"{btn_name}: 0", width=60)
    label.pack(side="top")
    customtkinter.CTkButton(frame, text="-", width=30,
                            command=lambda k=btn_name: update_counter(teleop_counters, [teleop_counter_labels, teleop_counter_labels_extra], k, -1, teleop_history)).pack(side="left")
    customtkinter.CTkButton(frame, text="+", width=30,
                            command=lambda k=btn_name: update_counter(teleop_counters, [teleop_counter_labels, teleop_counter_labels_extra], k, 1, teleop_history)).pack(side="left")
    teleop_counter_labels[btn_name] = label
extra_frame_teleop = customtkinter.CTkFrame(teleop_frame)
extra_frame_teleop.pack(pady=10)
teleop_counter_labels_extra = {}
for key in extra_keys:
    frame = customtkinter.CTkFrame(extra_frame_teleop)
    frame.pack(side="left", padx=5)
    label = customtkinter.CTkLabel(frame, text=f"{key}: 0", width=80)
    label.pack(side="top")
    customtkinter.CTkButton(frame, text="-", width=30,
                            command=lambda k=key: update_counter(teleop_counters, [teleop_counter_labels, teleop_counter_labels_extra], k, -1, teleop_history)).pack(side="left")
    customtkinter.CTkButton(frame, text="+", width=30,
                            command=lambda k=key: update_counter(teleop_counters, [teleop_counter_labels, teleop_counter_labels_extra], k, 1, teleop_history)).pack(side="left")
    teleop_counter_labels_extra[key] = label
# Toggle broken state button
def toggle_broken():
    global teleop_broken_state
    teleop_broken_state = "Yes" if teleop_broken_state == "No" else "No"
    broken_btn.configure(text=f"Broken: {teleop_broken_state}")
    teleop_history.append(("broken", teleop_broken_state))
broken_btn = customtkinter.CTkButton(teleop_frame, text=f"Broken: {teleop_broken_state}",
                                     width=150, command=toggle_broken)
broken_btn.pack(pady=5)
climb_dropdown = customtkinter.CTkComboBox(teleop_frame, values=["No barge", "Barge", "Shallow climb", "Deep climb"],
                                           command=lambda val: set_climb_state(val))
climb_dropdown.set("No barge")
climb_dropdown.pack(pady=5)
teleop_comment_box = customtkinter.CTkTextbox(teleop_frame, width=300, height=100, wrap="word")
teleop_comment_box.pack(pady=5)
teleop_comment_box.bind("<KeyRelease>", lambda event: update_comment_count(teleop_comment_box, teleop_comment_count_label, event))
teleop_comment_count_label = customtkinter.CTkLabel(teleop_frame, text=f"{MAX_COMMENT_LENGTH} characters remaining")
teleop_comment_count_label.pack(anchor="e", padx=10)
customtkinter.CTkButton(teleop_frame, text="End Match", width=150, command=end_match).pack(pady=5)

# Only one definition of set_climb_state is needed.
def set_climb_state(val):
    global climb_state
    climb_state = val

root.mainloop()
