from tkinter import *
from tkinter import simpledialog, messagebox, colorchooser, filedialog
import json, csv, datetime, os

root_window = Tk()
root_window.title("Weekly Calendar")
root_window.minsize(700, 500)

label_planner = Label(root_window, text="Study Planner", font=("Arial", 11, "bold"))
label_planner.pack(side="top")

calendar_frame = Frame(root_window)
calendar_frame.pack(fill="both", expand=True)

days = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
times = []
for h in range(8, 18):
    times.append(f"{h}:00")
    times.append(f"{h}:30")

cells = {}
courses_colors = {}
sessions = {}
colors = ["lightgreen", "lightyellow", "lightpink", "lightgray", "lightcoral", "lightcyan"]
color_index = 0
notes = []  # list to store note entries
NOTE_ICON = '📝'  # icon to mark notes on calendar cells
choice_dialog_current = None  # track the open choice dialog Toplevel


# --- Create the table ---
def create_table():
    for col, day in enumerate(days):
        header = Label(calendar_frame, text=day, font=("Arial", 11), borderwidth=1,
                       relief="solid", width=15, bg="lightblue")
        header.grid(row=0, column=col, sticky="nsew")

    for row, time in enumerate(times, start=1):
        time_label = Label(calendar_frame, text=time, font=("Arial", 11),
                           borderwidth=1, relief="solid", width=15)
        time_label.grid(row=row, column=0, sticky="nsew")

        for col in range(1, len(days)):
            cell = Label(calendar_frame, text="", font=("Arial", 11),
                         borderwidth=1, relief="solid", width=15)
            cell.grid(row=row, column=col, sticky="nsew")
            cell.bind("<Button-1>", lambda e, r=row, c=col: click_on_cell(r, c))
            cells[(row, col)] = cell

    # Scale table properly
    for d in range(len(days)):
        calendar_frame.grid_columnconfigure(d, weight=1)
    for t in range(len(times) + 1):
        calendar_frame.grid_rowconfigure(t, weight=1)

# --- Helper: Popup for edit/delete ---
def edit_or_delete_popup():
    popup = Toplevel()
    popup.title("Choose Action")
    popup.minsize(width=200, height=120)
    choice = {"value": None}

    def set_choice(option):
        choice["value"] = option
        popup.destroy()

    Label(popup, text="Do you want to edit or delete this session?").pack(pady=10)
    Button(popup, text="Edit", width=10, command=lambda: set_choice("edit")).pack(pady=5)
    Button(popup, text="Delete", width=10, command=lambda: set_choice("delete")).pack(pady=5)
    Button(popup, text="Cancel", width=10, command=lambda: set_choice("cancel")).pack(pady=5)

    popup.wait_window()
    return choice["value"]

# --- Helper: Ask for session length ---
def study_length(row, col):
    session_length_str = simpledialog.askstring(
        "Input",
        "Enter session length in 30-min blocks (1=30 min, 2=1 hr, etc):",
        parent=root_window
    )
    if not session_length_str or not session_length_str.isdigit():
        messagebox.showerror("Error", "Invalid session length.")
        return None

    session_length = int(session_length_str)
    if session_length < 1 or row + session_length - 1 > len(times):
        messagebox.showerror("Error", "Session too long for timetable.")
        return None

    # Clear existing session for that column (same course region)
    for key in list(sessions.keys()):
        if key[1] == col and key[0] >= row and cells[key].cget("text") != "":
            cells[key].config(text="", bg="SystemButtonFace")
            sessions.pop(key, None)

    return session_length

# --- Helper: Choose color and fill cells ---
def color_choice(course, row, col, session_length):
    global color_index
    if course not in courses_colors:
        color = colorchooser.askcolor(title=f"Choose color for {course}")[1]
        if not color:
            color = colors[color_index % len(colors)]
        courses_colors[course] = color
        color_index += 1
    color = courses_colors[course]

    # Fill cells
    for l in range(session_length):
        target_row = row + l
        key = (target_row, col)
        sessions[key] = {"course": course, "color": color}
        cell = cells.get(key)
        if cell:
            cell.config(text=course if l == 0 else "", bg=color)

# --- Handle clicks on cells ---
def click_on_cell(row, col):
    global choice_dialog_current
    # destroy existing choice dialog if still open
    if choice_dialog_current is not None:
        try:
            choice_dialog_current.destroy()
        except:
            pass
        choice_dialog_current = None
    # first ask whether to add session or note
    choice_dialog = Toplevel(root_window)
    choice_dialog_current = choice_dialog
    choice_dialog.title("What would you like to add?")
    choice_dialog.minsize(width=200, height=120)
    sel = {"value": None}
    def set_sel(v): sel["value"] = v; choice_dialog.destroy();
    Button(choice_dialog, text="Add Note", width=12, command=lambda:set_sel("note")).pack(pady=5)
    Button(choice_dialog, text="Add Session", width=12, command=lambda:set_sel("session")).pack(pady=5)
    Button(choice_dialog, text="Cancel", width=12, command=lambda:set_sel(None)).pack(pady=5)
    choice_dialog.wait_window()
    action = sel.get("value")
    if action == "note":
        add_note(row, col)
        return
    if action != "session":
        return
    cell_key = (row, col)

    # if there is a study session in the cell, run the edit_or_delete_pop_up() function
    if cell_key in sessions:
        choice = edit_or_delete_popup()
        if choice == "edit":
            if not courses:
                messagebox.showerror("Error", "No courses available. Add courses first in Manage Courses.")
                return

            # Choose the course
            course_selection = Toplevel(root_window)
            course_selection.title("Select Course")
            course_selection.geometry("300x200")
            Label(course_selection, text="Select course for this session:").pack(pady=10)

            selected_course = {"name": None}

            def select_course(name):
                selected_course["name"] = name
                course_selection.destroy()

            for course_name in courses.keys():
                Button(course_selection, text=course_name, width=20, command=lambda n=course_name: select_course(n)).pack(pady=2)

            course_selection.wait_window()
            course = selected_course["name"]
            if not course:
                return

            # Ask the study length
            session_length = study_length(row, col)
            if session_length is None:
                return

            # Edit the color and study length
            color_choice(course, row, col, session_length)
        elif choice == "delete":
            course_to_delete = sessions[cell_key]["course"]
            for key in list(sessions.keys()):
                if sessions[key]["course"] == course_to_delete and key[1] == col:
                    sessions.pop(key)
                    cells[key].config(text="", bg="SystemButtonFace")
        return

    # if there isn't a study session planned, add new one
    if not courses: #if there arent any courses yet -> error
        messagebox.showerror("Error", "No courses available. Add courses first in Manage Courses.")
        return

    course_selection = Toplevel(root_window)
    course_selection.title("Select Course")
    course_selection.geometry("300x200")
    Label(course_selection, text="Select course for this session:").pack(pady=10)

    selected_course = {"name": None}

    def select_course(name):
        selected_course["name"] = name
        course_selection.destroy()

    for course_name in courses.keys():
        Button(course_selection, text=course_name, width=20, command=lambda n=course_name: select_course(n)).pack(pady=2)

    course_selection.wait_window()
    course = selected_course["name"]
    if not course:
        return

    session_length = study_length(row, col)
    if session_length is None:
        return
    color_choice(course, row, col, session_length)

# --- MENU ---
def setup_menu():
    menubar = Menu(root_window)
    root_window.config(menu=menubar)

    # --- Study Planner Menu ---
    study_menu = Menu(menubar, tearoff=0)
    study_menu.add_command(label="Open Planner", command=lambda: show_section("Study Planner"))
    study_menu.add_separator()
    study_menu.add_command(label="Exit", command=root_window.quit)
    menubar.add_cascade(label="Study Planner", menu=study_menu)
    study_menu.add_command(label="Manage Courses", command=manage_courses)

    # --- Course Hour Tracker Menu ---
    tracker_menu = Menu(menubar, tearoff=0)
    tracker_menu.add_command(label="Open Tracker", command=open_course_tracker)
    menubar.add_cascade(label="Course Hour Tracker", menu=tracker_menu)

    # --- Note System Menu ---
    notes_menu = Menu(menubar, tearoff=0)
    notes_menu.add_command(label="Open Notes", command=open_notes_system)
    menubar.add_cascade(label="Note System", menu=notes_menu)

    # --- Flashcards ---
    flash_pomo_menu = Menu(menubar, tearoff=0)
    flash_pomo_menu.add_command(label="Open Flashcards", command=lambda: show_section("Flashcards"))
    flash_pomo_menu.add_command(label="Open Quiz", command=lambda: show_section("Quiz"))
    menubar.add_cascade(label="Flashcards & Quizzes", menu=flash_pomo_menu)

    # --- Pomodoro timer ---
    flash_pomo_menu = Menu(menubar, tearoff=0)
    flash_pomo_menu.add_command(label="Open Pomodoro Timer", command=lambda: show_section("Pomodoro Timer"))
    menubar.add_cascade(label="Pomodoro timer", menu=flash_pomo_menu)

# --- Placeholder: Show selected section ---
def show_section(name):
    messagebox.showinfo("Section", f"{name} feature will be added soon!")

# --- Note System functions -----------------------------------------
def add_note(row, col):
    dialog = Toplevel(root_window)
    dialog.title("Add Note")
    dialog.minsize(width=250, height=150)
    choice = {"value": None}
    def set_choice(v): choice["value"] = v; dialog.destroy()
    Label(dialog, text="Select note type:").pack(pady=10)
    Button(dialog, text="Text", width=10, command=lambda: set_choice("text")).pack(pady=5)
    Button(dialog, text="File", width=10, command=lambda: set_choice("file")).pack(pady=5)
    Button(dialog, text="Audio", width=10, command=lambda: set_choice("audio")).pack(pady=5)
    dialog.wait_window()
    typ = choice.get("value")
    if not typ:
        return
    content = None
    if typ == "text":
        content = simpledialog.askstring("Input", "Enter note text:", parent=root_window)
        if not content:
            return
    else:
        filetypes = [("All files", "*.*")]
        if typ == "audio":
            filetypes = [("Audio files", "*.mp3 *.wav"), ("All files", "*.*")]
        content = filedialog.askopenfilename(title="Select file", filetypes=filetypes)
        if not content:
            return
    note = {
        "date": datetime.date.today().isoformat(),
        "time": times[row-1],
        "day": days[col],
        "type": typ,
        "content": content
    }
    notes.append(note)
    # mark icon on corresponding calendar cell
    cell = cells.get((row, col))
    if cell:
        current = cell.cget('text')
        if NOTE_ICON not in current:
            new_text = f"{current} {NOTE_ICON}".strip()
            cell.config(text=new_text)
    messagebox.showinfo("Note Added", "Your note has been added.")

def open_notes_system():
    ns = Toplevel(root_window)
    ns.title("Note System")
    ns.geometry("400x300")
    Label(ns, text="All Notes", font=("Arial", 12, "bold")).pack(pady=5)
    listbox = Listbox(ns)
    listbox.pack(fill="both", expand=True, padx=10, pady=5)
    for i, note in enumerate(notes, start=1):
        summary = f"{i}. {note['date']} {note['day']} {note['time']} [{note['type']}]"
        listbox.insert(END, summary)
    # bind double-click to view note detail
    def view_note(event):
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        note = notes[idx]
        if note['type'] == 'text':
            messagebox.showinfo("Note", note['content'])
        else:
            # open file or audio with default application
            path = note['content']
            try:
                os.startfile(path)
            except Exception as e:
                messagebox.showerror("Error", f"Cannot open file: {e}")
    listbox.bind('<Double-Button-1>', view_note)
    btn_frame = Frame(ns)
    btn_frame.pack(pady=5)
    Button(btn_frame, text="Save JSON", command=save_notes_json).pack(side="left", padx=5)
    Button(btn_frame, text="Save CSV", command=save_notes_csv).pack(side="left", padx=5)

def save_notes_json():
    if not notes:
        messagebox.showwarning("No Notes", "There are no notes to save.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
    if not file:
        return
    with open(file, "w") as f:
        json.dump(notes, f, indent=4)
    messagebox.showinfo("Saved", f"Notes saved to {file}")

def save_notes_csv():
    if not notes:
        messagebox.showwarning("No Notes", "There are no notes to save.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
    if not file:
        return
    keys = ["date","day","time","type","content"]
    with open(file, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for note in notes:
            writer.writerow(note)
    messagebox.showinfo("Saved", f"Notes saved to {file}")



# --- COURSE HOUR TRACKER WINDOW ---
def open_course_tracker():
    tracker_window = Toplevel(root_window)
    tracker_window.title("Course Tracker")
    tracker_window.geometry("400x300")

    Label(tracker_window, text="Course Tracker", font=("Arial", 12, "bold")).pack(pady=5)

    # Frame for table
    table_frame = Frame(tracker_window)
    table_frame.pack(padx=10, pady=10, fill="both", expand=True)

    # Header
    Label(table_frame, text="Course", font=("Arial", 11, "bold"), borderwidth=1, relief="solid", width=20, bg="lightblue").grid(row=0, column=0)
    Label(table_frame, text="Tracked Hours", font=("Arial", 11, "bold"), borderwidth=1, relief="solid", width=15, bg="lightblue").grid(row=0, column=1)

    # Bereken aantal geplande uren per vak
    course_hours = {}
    for key, info in sessions.items():
        course = info["course"]
        # 30 minuten per blok = 0.5 uur
        course_hours[course] = course_hours.get(course, 0) + 0.5

    # Vul tabel
    for i, (course, hours) in enumerate(course_hours.items(), start=1):
        Label(table_frame, text=course, borderwidth=1, relief="solid", width=20).grid(row=i, column=0)
        Label(table_frame, text=str(hours), borderwidth=1, relief="solid", width=15).grid(row=i, column=1)

    # Als er nog geen data is
    if not course_hours:
        Label(tracker_window, text="Nog geen sessies gepland.", fg="gray").pack(pady=20)

# --- 1. Courses dictionary (bovenaan, naast courses_colors) ---
courses = {}  # course_name -> color

# --- 2. Manage Courses venster ---
def manage_courses():
    mc_window = Toplevel(root_window)
    mc_window.title("Manage Courses")
    mc_window.geometry("400x300")

    Label(mc_window, text="Manage Courses", font=("Arial", 12, "bold")).pack(pady=5)

    list_frame = Frame(mc_window)
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)

    listbox = Listbox(list_frame)
    listbox.pack(side="left", fill="both", expand=True)

    scrollbar = Scrollbar(list_frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=listbox.yview)

    # Populate listbox
    for course in courses.keys():
        listbox.insert(END, course)

    # --- Add course ---
    def add_course():
        course_name = simpledialog.askstring("Add Course", "Enter course name:", parent=mc_window)
        if not course_name:
            return
        if course_name in courses:
            messagebox.showerror("Error", "Course already exists.")
            return
        color = colorchooser.askcolor(title=f"Choose color for {course_name}")[1]
        if not color:
            global color_index
            color = colors[color_index % len(colors)]
        courses[course_name] = color
        courses_colors[course_name] = color
        listbox.insert(END, course_name)

    # --- Edit course ---
    def edit_course():
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No course selected.")
            return

        old_name = listbox.get(selection[0])
        new_name = simpledialog.askstring("Edit Course", "Enter new course name:", initialvalue=old_name,
                                          parent=mc_window)
        if not new_name:
            return

        color = colorchooser.askcolor(title=f"Choose color for {new_name}")[1] or courses_colors[old_name]

        # Update course dictionaries
        courses[new_name] = color
        courses_colors[new_name] = color
        if new_name != old_name:
            courses.pop(old_name)
            courses_colors.pop(old_name)

        # Update all existing sessions in the planner
        for key, info in sessions.items():
            if info["course"] == old_name:
                info["course"] = new_name
                info["color"] = color
                cell = cells[key]
                # Alleen de eerste cel van de sessie toont de naam
                first_cell_of_session = True
                # Check if there is a cell above with the same course
                above_key = (key[0] - 1, key[1])
                if above_key in sessions and sessions[above_key]["course"] == old_name:
                    first_cell_of_session = False
                cell.config(text=new_name if first_cell_of_session else "", bg=color)

        # Update listbox
        listbox.delete(selection[0])
        listbox.insert(selection[0], new_name)

    # --- Delete course ---
    def delete_course():
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No course selected.")
            return
        course_to_delete = listbox.get(selection[0])
        confirm = messagebox.askyesno("Confirm", f"Delete course '{course_to_delete}' and all its sessions?")
        if not confirm:
            return
        # Remove from sessions
        for key in list(sessions.keys()):
            if sessions[key]["course"] == course_to_delete:
                sessions.pop(key)
                cells[key].config(text="", bg="SystemButtonFace")
        courses.pop(course_to_delete)
        courses_colors.pop(course_to_delete)
        listbox.delete(selection[0])

    # Buttons
    btn_frame = Frame(mc_window)
    btn_frame.pack(pady=10)
    Button(btn_frame, text="Add", width=10, command=add_course).grid(row=0, column=0, padx=5)
    Button(btn_frame, text="Edit", width=10, command=edit_course).grid(row=0, column=1, padx=5)
    Button(btn_frame, text="Delete", width=10, command=delete_course).grid(row=0, column=2, padx=5)


# --- RUN ---
create_table()
setup_menu()
root_window.mainloop()


