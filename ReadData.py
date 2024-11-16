import os
import customtkinter
from tkinter import messagebox
from PIL import Image, ImageTk

# Initialize global variables
data_file = "Data/data.txt"
entries = []
current_index = 0


# Read the data from the file
def read_data():
    global entries
    if not os.path.exists(data_file):
        print("Data file does not exist.")
        return

    with open(data_file, "r") as file:
        lines = file.readlines()
        entries = []
        for line in lines:
            line = line.strip()
            if line:
                # Check if the line has the correct number of parts after splitting
                parts = line.split(" | ")
                if len(parts) == 5:  # Ensure there are exactly 5 parts
                    entries.append(parts)
                else:
                    print(f"Skipping malformed line: {line}")


# Display the current team's data in the GUI
def display_team_data(index):
    if index < 0 or index >= len(entries):
        print("Index out of range, unable to display data.")
        return

    team_data = entries[index]

    # Ensure team_data has at least 5 parts to prevent index errors
    if len(team_data) >= 5:
        print(f"Displaying data for: {team_data}")
        match_number.set(team_data[0].split(" ")[1])  # Match number from "MATCH X"
        team_number.set(team_data[2])  # Directly set the team number (no split needed)
        score_label.configure(text=f"Score: {team_data[3]}")  # Score
        notes_entry.delete(1.0, 'end')
        notes_entry.insert('end', team_data[4])  # Notes

        # Get the coordinates and display red X on map
        coords = team_data[4].split(":")[1].strip()  # Extract coordinates from "Coordinates: (x, y)"
        coords = coords[1:-1].split(",")  # Extract x and y from (x, y)

        # Update the map with a red X at the coordinates
        display_map(coords)
    else:
        print(f"Invalid team data: {team_data}")


# Function to display the map with a red X at the coordinates
def display_map(coords):
    x, y = map(int, coords)

    # Redraw the image and draw the red X at the coordinates
    img = Image.open("Data/Map2024.png")
    img = img.resize((600, 259))  # Resize the image to the correct ratio
    img = ImageTk.PhotoImage(img)

    # Update the image on the label
    image_label.configure(image=img)
    image_label.image = img

    # Create a canvas to draw a red X
    canvas.create_oval(x - 5, y - 5, x + 5, y + 5, outline="red", width=2)


# Callback to move to the next team
def next_team():
    global current_index
    if current_index < len(entries) - 1:
        current_index += 1
        display_team_data(current_index)


# Callback to move to the previous team
def prev_team():
    global current_index
    if current_index > 0:
        current_index -= 1
        display_team_data(current_index)


# Callback to submit and save the data
def submit_data():
    match_number_value = match_number.get()
    team_number_value = team_number.get()
    score_value = score_label.cget("text").split(":")[1].strip()
    notes_value = notes_entry.get(1.0, 'end-1c')

    # Prepare the new data to save to file
    new_data = f"MATCH {match_number_value} | {alliance.get()} | {team_number_value} | {score_value} | Coordinates: {coordinates} Notes: {notes_value}\n"

    with open(data_file, "a") as file:
        file.write(new_data)

    messagebox.showinfo("Data Submitted", "The data has been successfully submitted.")


# GUI setup
app = customtkinter.CTk()

# Read data from file
read_data()

# Set up main window size and title
app.geometry("800x600")
app.title("Team Scouting")

# Top row with match number, team number, and alliance
frame_top = customtkinter.CTkFrame(app)
frame_top.pack(fill="x", pady=10)

# Match number and team number
match_number = customtkinter.StringVar()
team_number = customtkinter.StringVar()
alliance = customtkinter.StringVar()

match_entry = customtkinter.CTkEntry(frame_top, textvariable=match_number, width=150, placeholder_text="Match Number")
match_entry.grid(row=0, column=0, padx=10)

team_entry = customtkinter.CTkEntry(frame_top, textvariable=team_number, width=150, placeholder_text="Team Number")
team_entry.grid(row=0, column=1, padx=10)

alliance_entry = customtkinter.CTkEntry(frame_top, textvariable=alliance, width=150, placeholder_text="Alliance")
alliance_entry.grid(row=0, column=2, padx=10)

# Arrows to cycle through teams
prev_button = customtkinter.CTkButton(frame_top, text="<", command=prev_team)
prev_button.grid(row=0, column=3, padx=10)

next_button = customtkinter.CTkButton(frame_top, text=">", command=next_team)
next_button.grid(row=0, column=4, padx=10)

# Map and red X in the middle
frame_middle = customtkinter.CTkFrame(app)
frame_middle.pack(expand=True, fill="both", padx=20, pady=10)

# Canvas for the map
canvas = customtkinter.CTkCanvas(frame_middle, width=600, height=259)
canvas.pack(pady=20)

image_label = customtkinter.CTkLabel(frame_middle)
image_label.pack()

# Score label and notes
frame_bottom = customtkinter.CTkFrame(app)
frame_bottom.pack(fill="x", pady=10)

score_label = customtkinter.CTkLabel(frame_bottom, text="Score: 0")
score_label.pack(pady=10)

notes_entry = customtkinter.CTkTextbox(frame_bottom, width=500, height=100)
notes_entry.pack(pady=10)

# Submit button
submit_button = customtkinter.CTkButton(frame_bottom, text="Submit", command=submit_data)
submit_button.pack()

# Display initial team data
display_team_data(current_index)

# Start the GUI main loop
app.mainloop()
