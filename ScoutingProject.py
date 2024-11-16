import os
import customtkinter
from PIL import Image, ImageTk

new_score = 0  # Initial score
score_list = []  # List to store scores and coordinates
image_label = None  # Variable to store image label


# Function to save data to a text file and clear the inputs
def save_to_text_file_and_clear(match_number, team_number, alliance_value, score, coordinates):
    folder_path = "data"
    file_path = os.path.join(folder_path, "data.txt")

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    with open(file_path, "a") as file:
        for score_data in score_list:
            match_number, alliance_value, team_number, score, coords = score_data
            file.write(f"MATCH {match_number} | {alliance_value} | {team_number} | {score} | Coordinates: {coords}\n")
    print(f"Data saved to {file_path}.")

    # Clear fields except Match Number
    teamNumber.delete(0, 'end')
    alliance.delete(0, 'end')
    global new_score
    new_score = 0
    score_label.configure(text=f"Score: {new_score}")
    score_list.clear()  # Clear the score list

    show_confirmation_message()


# Callback function for submit button
def submit():
    match_number = matchNumber.get()
    team_number = teamNumber.get()
    alliance_value = alliance.get()
    save_to_text_file_and_clear(match_number, team_number, alliance_value, new_score, score_list)


# Function to show confirmation message after submission
def show_confirmation_message():
    confirmation_label.configure(text="Data Submitted")
    confirmation_label.after(2000, clear_confirmation_message)  # Clear message after 2 seconds


# Function to clear confirmation message
def clear_confirmation_message():
    confirmation_label.configure(text="")


# Callback function for score button
def increment_score():
    global new_score
    new_score += 1
    score_label.configure(text=f"Score: {new_score}")

    # Display the map in the same window after scoring
    display_map()


# Function to display the map in the same window
def display_map():
    img = Image.open("Data/Map2024.png")  # Corrected path to the image

    # Calculate the height based on the aspect ratio 600:259
    width = 600
    height = int(259 / 600 * width)  # Maintain aspect ratio
    img = img.resize((width, height))  # Resize the image
    img_tk = ImageTk.PhotoImage(img)

    # Update or create the label to display the image
    global image_label
    if image_label is not None:
        image_label.grid_remove()  # Remove previous image if it exists

    image_label = customtkinter.CTkLabel(app, image=img_tk)
    image_label.image = img_tk  # Keep a reference to the image
    image_label.grid(row=2, column=0, padx=20, pady=20, columnspan=3)
    image_label.bind("<Button-1>", lambda event: capture_click(event))


# Function to capture the click on the image
def capture_click(event):
    # Get the coordinates of the click relative to the image
    x = event.x
    y = event.y

    # Display the coordinates on the window or log them for later submission
    coords = f"({x}, {y})"

    # Add the score and coordinates to the list
    score_list.append((matchNumber.get(), alliance.get(), teamNumber.get(), new_score, coords))

    # Optionally, show a temporary message with the coordinates
    print(f"Clicked at {coords} for score {new_score}")

    # Remove the image after clicking
    image_label.grid_remove()

    # Swap back to the score tracker window after clicking on the map
    frame_notes.grid_remove()  # Make sure notes screen is hidden
    frame_score.grid()  # Show the score tracking screen again
    teamNumber.focus()  # Focus on the team number field


# Function to swap screens between score tracking and notes entry
def swap_screen(event=None):
    if frame_score.winfo_viewable():
        frame_score.grid_remove()
        frame_notes.grid()
        notes_entry.focus()  # Focus on the notes entry when switching
    else:
        frame_notes.grid_remove()
        frame_score.grid()
        teamNumber.focus()


# GUI setup
app = customtkinter.CTk()
app.geometry("600x500")
app.title("Match Scoring App")

# Top Section: Match Number, Alliance, and Team Number Inputs (beside each other)
matchNumber = customtkinter.CTkEntry(app, placeholder_text="Match Number", width=180)
matchNumber.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="n")

alliance = customtkinter.CTkEntry(app, placeholder_text="Alliance", width=180)
alliance.grid(row=0, column=1, padx=(10, 10), pady=(20, 10), sticky="n")

teamNumber = customtkinter.CTkEntry(app, placeholder_text="Team Number", width=180)
teamNumber.grid(row=0, column=2, padx=(10, 20), pady=(20, 10), sticky="n")

# Middle Section: Score and Buttons (aligned to the center)
frame_score = customtkinter.CTkFrame(app)
frame_score.grid(row=1, column=0, padx=20, pady=20, sticky="nsew", columnspan=3)

# Add Score label
score_label = customtkinter.CTkLabel(frame_score, text=f"Score: {new_score}", font=("Arial", 16))
score_label.grid(row=0, column=0, padx=20, pady=10)

# Add Score button
score_button = customtkinter.CTkButton(frame_score, text="+1 Score", command=increment_score, width=100)
score_button.grid(row=1, column=0, padx=20, pady=10)

# Notes Entry Frame (centered and with a larger text box)
frame_notes = customtkinter.CTkFrame(app)
frame_notes.grid(row=2, column=0, padx=20, pady=20, columnspan=3, sticky="nsew")

# Make sure the grid of the notes frame is set to fill the space properly
frame_notes.grid_rowconfigure(0, weight=1)
frame_notes.grid_columnconfigure(0, weight=1)

# Use Text widget for multiline input with wrapping
notes_entry = customtkinter.CTkTextbox(frame_notes, width=500, height=200)
notes_entry.grid(row=0, column=0, padx=20, pady=20)

# Bottom Section: Submit Button (aligned to center)
submit_button = customtkinter.CTkButton(app, text="Submit", command=submit, width=200)
submit_button.grid(row=3, column=0, padx=20, pady=20, sticky="s", columnspan=3)

# Confirmation message label at the bottom
confirmation_label = customtkinter.CTkLabel(app, text="")
confirmation_label.grid(row=4, column=0, padx=10, pady=10, columnspan=3)

# Initially show only the score tracking frame
frame_notes.grid_remove()

# Bind the Ctrl key to swap screens
app.bind("<Control_L>", swap_screen)
app.bind("<Control_R>", swap_screen)

# Expand middle frame to fill the window
app.grid_rowconfigure(1, weight=1)
app.grid_columnconfigure(0, weight=1)

app.mainloop()
