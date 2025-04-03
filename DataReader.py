import cv2
import json
from pyzbar import pyzbar
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Provided credentials
SPREADSHEET_ID = "12PUHwWSQQou5LjnwuTT-mEWn5Z42Ixny6Z-MZ8DhpDY"
SHEET_NAME = "Raw"
CREDENTIALS_PATH = "bubblescout-07b081651c6e.json"

def flatten_data(data):
    # Info columns: Match, Team, Alliance, Scout Name
    info = [
        data.get("match_number", ""),
        data.get("team_number", ""),
        data.get("selected_color", ""),
        data.get("scouter_name", "")
    ]
    # Auto columns: L1, L2, L3, L4, Algae Removed, Algae Processed, Algae Netted, Move State, Starting Pos, Comment
    auto = data.get("auto", {})
    auto_counters = auto.get("counters", {})
    auto_values = [
        auto_counters.get("L1", 0),
        auto_counters.get("L2", 0),
        auto_counters.get("L3", 0),
        auto_counters.get("L4", 0),
        auto_counters.get("Algae Removed", 0),
        auto_counters.get("Algae Processed", 0),
        auto_counters.get("Algae Netted", 0),
        auto.get("moved_state", ""),
        ",".join(map(str, auto.get("robot_coords", []))),
        auto.get("comment", "")
    ]
    # TeleOp columns: L1, L2, L3, L4, Algae Removed, Algae Processed, Algae Netted, Climb State, Broken, Comment
    teleop = data.get("teleop", {})
    teleop_counters = teleop.get("counters", {})
    teleop_values = [
        teleop_counters.get("L1", 0),
        teleop_counters.get("L2", 0),
        teleop_counters.get("L3", 0),
        teleop_counters.get("L4", 0),
        teleop_counters.get("Algae Removed", 0),
        teleop_counters.get("Algae Processed", 0),
        teleop_counters.get("Algae Netted", 0),
        teleop.get("climb_state", ""),
        teleop.get("teleop_broken_state", ""),
        teleop.get("comment", "")
    ]
    return info + auto_values + teleop_values

def update_google_sheet(json_data):
    # Authenticate and open the spreadsheet
    scope = ['https://www.googleapis.com/auth/spreadsheets',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_PATH, scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        sheet = spreadsheet.worksheet(SHEET_NAME)
    except gspread.exceptions.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title=SHEET_NAME, rows="100", cols="26")
    # If the sheet is empty, add headers in two rows
    if not sheet.row_values(1):
        header_row1 = ["Info", "", "", "", "Auto", "", "", "", "", "", "", "", "", "", "TeleOp", "", "", "", "", "", "", "", "", "", ""]
        header_row2 = ["Match", "Team", "Alliance", "Scout Name",
                       "L1", "L2", "L3", "L4", "Algae Removed", "Algae Processed", "Algae Netted", "Move State",
                       "Starting Pos", "Comment",
                       "L1", "L2", "L3", "L4", "Algae Removed", "Algae Processed", "Algae Netted", "Climb State",
                       "Broken", "Comment"]
        sheet.update("A1:X2", [header_row1, header_row2])
    # Flatten the data in the correct order
    flattened = flatten_data(json_data)
    sheet.append_row(flattened, value_input_option="USER_ENTERED")
    print("Data sent to Google Sheets successfully.")

def read_qr_codes_from_camera():
    temp_data = []  # Temporary storage for unique entries
    cap = cv2.VideoCapture(0)  # Open default camera
    print("Starting QR code scanning. Press 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Decode all QR codes in the frame
        codes = pyzbar.decode(frame)
        # Sort codes left to right based on x coordinate
        codes = sorted(codes, key=lambda c: c.rect.left)

        for code in codes:
            data_str = code.data.decode("utf-8")
            try:
                data = json.loads(data_str)
                # Create a unique key based on (scouter_name, match_number, team_number)
                key = (data.get("scouter_name", ""), data.get("match_number", ""), data.get("team_number", ""))
                keys_existing = [(d.get("scouter_name", ""), d.get("match_number", ""), d.get("team_number", "")) for d in temp_data]
                if key not in keys_existing:
                    temp_data.append(data)
                    print("New entry added:")
                    print(json.dumps(data, indent=4))
                else:
                    print("Duplicate entry found; ignoring.")
            except Exception as e:
                print("Error decoding QR code data:", e)

        # Optionally, display the frame with bounding boxes
        for code in codes:
            (x, y, w, h) = code.rect
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.imshow("QR Code Scanner", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return temp_data

if __name__ == "__main__":
    scanned_data = read_qr_codes_from_camera()
    print("\nFinal unique QR data:")
    for entry in scanned_data:
        print(json.dumps(entry, indent=4))
        # Send each unique entry to the Google spreadsheet.
        update_google_sheet(entry)
