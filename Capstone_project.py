# ONE THING TO CONSIDER IS THE DELETE OF COURSES WHEN THE TRACKER IS OPENED. THIS DOESNOT WORK!!!
# ANOTHER THING IS THE SPACE ABOVE THE PLANNER WHEN OPENED IN FULL SCREEN

#when editing courses and changing the time spent on the new course to less than the first input the colors stay -Feie

from tkinter import *
from tkinter import simpledialog, messagebox, colorchooser, filedialog
import winsound
import datetime
import json
import csv
import os


# --- MAIN WINDOW SETUP ---
root_window = Tk()
root_window.title("Weekly Calendar")
root_window.minsize(700, 500)

calendar_frame = Frame(root_window)
calendar_frame.pack(fill="both", expand=True)

days = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
times = []
for h in range(8, 18):
    times.append(f"{h}:00")
    times.append(f"{h}:30")

# --- DICTIONARIES TO KEEP DATA ---
cells = {}             # Stores the Label widgets (each table cell)
sessions = {}          # Stores scheduled study sessions
courses = {}           # Stores course names and colors
course_colors = {}     # Stores color for each course
tracked_hours = {}     # Stores accumulated Pomodoro study time per course

# --- DEFAULT COURSES AT STARTUP ---
default_courses = ["Math", "History", "Biology"]
default_colors = ["lightpink", "lightyellow", "lightgreen"]

for name, color in zip(default_courses, default_colors):
    courses[name] = color
    course_colors[name] = color

# Default color list to use if user doesn’t pick one
colors = ["lightgray", "lightcoral", "lightcyan", "yellow", "green", "pink",]
color_index = 0

# --- GLOBALS ---
main_frame = Frame(root_window)
main_frame.pack(fill="both", expand=True)

# ==========================
# NOTE SYSTEM (from Program 1, adapted for menu use)
# ==========================

import datetime, json, csv, os
from tkinter import Toplevel, StringVar, Text, Canvas, Frame, Label, END
from tkinter import filedialog, messagebox
from tkinter import ttk


notes = []
NOTE_ICON = "📝"

def _make_labeled(parent, widget_cls, label, **opts):
    frm = ttk.Frame(parent)
    frm.pack(fill="x", padx=20, pady=5)
    ttk.Label(frm, text=label).pack(side="left")
    w = widget_cls(frm, **opts)
    w.pack(side="left", fill="x", expand=True, padx=(5,0))
    return w

def launch_note_editor(parent, *, note=None, courses_list=None, title_text="New Note", subtitle_text=None):
    data = note.copy() if note else {}
    editor = Toplevel(parent)
    editor.title(title_text); editor.transient(parent); editor.grab_set()

    # Header
    ttk.Label(editor, text=title_text, font=("Arial",12,"bold")).pack(pady=(12,4))
    if subtitle_text:
        ttk.Label(editor, text=subtitle_text, font=("Arial",10)).pack(pady=(0,8))

    # Course dropdown first
    opts = ["General"] + [c for c in (courses_list or []) if c!="General"]
    if data.get("course") and data["course"] not in opts:
        opts.append(data["course"])
    course_var = StringVar(value=data.get("course") or "General")
    _make_labeled(editor, ttk.Combobox, "Course:", textvariable=course_var,
                 values=opts, state="readonly", width=25)

    # Title entry
    title_entry = _make_labeled(editor, ttk.Entry, "Title:")
    if data.get("title"):
        title_entry.insert(0, data["title"])

    # Description text box
    desc_frame = ttk.Frame(editor)
    ttk.Label(desc_frame, text="Description:").pack(anchor="w", padx=20, pady=(5,0))
    content_txt = Text(desc_frame, wrap="word", height=8)
    content_txt.pack(fill="both", expand=True, padx=20, pady=(0,5))
    if data.get("content") and data.get("type","text")=="text":
        content_txt.insert("1.0", data["content"])
    desc_frame.pack(fill="both", expand=True)

    # Attachment buttons: audio and file
    attachment_var = StringVar(value=(data.get("content") if data.get("type") in ["file","audio"] else ""))
    attachment_type = StringVar(value=(data.get("type") if data.get("type") in ["file","audio"] else ""))
    attach_frame = ttk.Frame(editor)
    attach_frame.pack(fill="x", padx=20, pady=5)
    def browse_file():
        path = filedialog.askopenfilename()
        if path:
            attachment_var.set(path)
            attachment_type.set("file")
    def browse_audio():
        path = filedialog.askopenfilename(filetypes=[("Audio Files","*.mp3 *.wav *.ogg")])
        if path:
            attachment_var.set(path)
            attachment_type.set("audio")
    # Audio icon button
    ttk.Button(attach_frame, text="🎤", width=3, command=browse_audio).pack(side="left", padx=(0,10))
    # File icon button
    ttk.Button(attach_frame, text="📁", width=3, command=browse_file).pack(side="left", padx=(0,10))
    ttk.Label(attach_frame, textvariable=attachment_var).pack(side="left", fill="x", expand=True)

    res = {}
    def _save():
        # Gather input values
        t = title_entry.get().strip()
        desc = content_txt.get("1.0",END).strip()
        attach = attachment_var.get().strip()
        # Require at least title or content (desc or attachment)
        if not t and not desc and not attach:
            messagebox.showerror("Missing Info","Enter title or content.",parent=editor)
            return
        # Determine note type and content
        if attach:
            nt = attachment_type.get() or 'file'
            content_val = attach
        else:
            nt = 'text'
            content_val = desc
        # Build result
        res['value'] = {
            "title": t,
            "content": content_val,
            "course": None if course_var.get()=="General" else course_var.get(),
            "type": nt
        }
        editor.destroy()

    btnf = ttk.Frame(editor)
    btnf.pack(pady=12)
    ttk.Button(btnf, text="Save",   command=_save).pack(side="left", padx=5)
    ttk.Button(btnf, text="Cancel", command=editor.destroy).pack(side="left", padx=5)
    editor.wait_window()
    return res.get("value")

def save_notes_json():
    if not notes:
        return messagebox.showwarning("No Notes","No notes to save.")
    path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON","*.json")])
    if not path: return
    with open(path,"w",encoding="utf-8") as f:
        json.dump(notes,f,indent=4,ensure_ascii=False)
    messagebox.showinfo("Saved",f"Notes saved to {path}")

def save_notes_csv():
    if not notes:
        return messagebox.showwarning("No Notes","No notes to save.")
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV","*.csv")])
    if not path: return
    keys = ["date","day","time","type","content"]
    with open(path,"w",newline="",encoding="utf-8") as f:
        writer = csv.DictWriter(f,fieldnames=keys)
        writer.writeheader()
        writer.writerows(notes)
    messagebox.showinfo("Saved",f"Notes saved to {path}")

def add_note_from_cell(row,col):
    vals = launch_note_editor(root_window, courses_list=list(courses.keys()),
                              title_text="New Note",
                              subtitle_text=f"{days[col]} • {times[row-1]}")
    if not vals: return
    now = datetime.datetime.now()
    note = {
        "date": now.date().isoformat(),
        "day": days[col],
        "time": times[row-1],
        "type": vals["type"],
        "content": vals["content"],
        "updated": now.isoformat()
    }
    if vals.get("title"):  note["title"]  = vals["title"]
    if vals.get("course"): note["course"] = vals["course"]
    notes.append(note)
    messagebox.showinfo("Note Added",f"Note added for {note['day']} at {note['time']}.")
    cell = cells.get((row,col))
    if cell and NOTE_ICON not in cell.cget("text"):
        cell.config(text=f"{cell.cget('text')} {NOTE_ICON}".strip())
    root_window.event_generate("<<NotesUpdated>>")

def add_note_from_notes_window(parent, note_index=None):
    note = notes[note_index] if note_index is not None and 0<=note_index<len(notes) else None
    vals = launch_note_editor(parent, note=note, courses_list=list(courses.keys()), title_text="Edit Note" if note else "New Note")
    if not vals: return
    now = datetime.datetime.now()
    new = {
        "date": note["date"] if note else now.date().isoformat(),
        "day":  note["day"]  if note else now.strftime("%A"),
        "time": note["time"] if note else now.strftime("%H:%M"),
        "type": note["type"] if note else "text",
        "content": vals["content"],
        "updated": now.isoformat()
    }
    if vals.get("title"):  new["title"]  = vals["title"]
    if vals.get("course"): new["course"] = vals["course"]
    if note_index is None or note is None:
        notes.append(new)
    else:
        notes[note_index] = new
    parent.event_generate("<<NotesUpdated>>")

def open_notes_system():
    ns = Toplevel(root_window); ns.title("Notes"); ns.geometry("720x520")
    ns.configure(bg="#fff")
    # Header
    hf = Frame(ns,bg="#fff"); hf.pack(fill="x",padx=20,pady=(20,10))
    Label(hf,text="Notes",font=("Arial",20,"bold"),bg="#fff",fg="#0f172a").pack(side="left")
    ttk.Button(hf,text="+ New Note",command=lambda:add_note_from_notes_window(ns)).pack(side="right")
    Label(hf,text=datetime.date.today().strftime("%A, %B %d, %Y"),font=("Arial",11),bg="#fff",fg="#475569").pack(anchor="w",pady=(4,0))

    # Scrollable area
    cf = Frame(ns,bg="#fff"); cf.pack(fill="both",expand=True)
    canvas = Canvas(cf,bg="#fff",highlightthickness=0)
    sb = ttk.Scrollbar(cf,orient="vertical",command=canvas.yview)
    canvas.configure(yscrollcommand=sb.set)
    sb.pack(side="right",fill="y"); canvas.pack(side="left",fill="both",expand=True)
    cards = Frame(canvas,bg="#fff")
    win = canvas.create_window((0,0),window=cards,anchor="nw")
    cards.bind("<Configure>",lambda e:canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win, width=e.width))
    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(-int(ev.delta/120), "units")))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    # Footer buttons
    ff = Frame(ns,bg="#fff"); ff.pack(fill="x",padx=20,pady=10)
    ttk.Button(ff,text="Save JSON",command=save_notes_json).pack(side="left",padx=(0,10))
    ttk.Button(ff,text="Save CSV", command=save_notes_csv).pack(side="left",padx=(0,10))
    ttk.Button(ff,text="Close",     command=ns.destroy).pack(side="right")

    def badge_colors(name):
        bg = course_colors.get(name,"#0ea5e9") if name else "#0ea5e9"
        r,g,b = ns.winfo_rgb(bg)
        bright = (0.299*r+0.587*g+0.114*b)/65535
        fg = "#0f172a" if bright>0.75 else "#fff"
        return bg, fg

    def open_item(obj):
        if obj["type"]=="text":
            w = Toplevel(ns); txt=Text(w,wrap="word",width=60,height=18)
            txt.insert("1.0",obj["content"]); txt.config(state="disabled"); txt.pack(fill="both",expand=True)
        else:
            try:
                os.startfile(obj["content"]) if os.name=="nt" else os.system(f'xdg-open "{obj["content"]}"')
            except Exception as e:
                messagebox.showerror("Error",f"Cannot open file: {e}",parent=ns)

    def render_card(idx,obj):
        cf = Frame(cards,bg="#fff",highlightthickness=1,highlightbackground="#e2e8f0")
        cf.pack(fill="x",padx=20,pady=10)
        trow = Frame(cf,bg="#fff"); trow.pack(fill="x",padx=20,pady=(18,6))
        bg,fg = badge_colors(obj.get("course"))
        Label(trow,text=obj.get("course") or "General",bg=bg,fg=fg,font=("Arial",10,"bold"),padx=10,pady=4).pack(side="left")
        act = Frame(trow,bg="#fff"); act.pack(side="right")
        ttk.Button(act,text="Edit",  width=6, command=lambda i=idx:add_note_from_notes_window(ns,i)).pack(side="left",padx=(0,6))
        ttk.Button(act,text="Delete",width=6, command=lambda i=idx:(notes.pop(i),ns.event_generate("<<NotesUpdated>>"))).pack(side="left")

        # Compute icon for attachment type
        icon = ""
        if obj.get("type") == "audio":
            icon = " 🎤"
        elif obj.get("type") == "file":
            # Show image icon for common image extensions
            ext = os.path.splitext(obj.get("content",""))[1].lower()
            if ext in [".png",".jpg",".jpeg",".gif",".bmp"]:
                icon = " 🖼️"
            else:
                icon = " 📁"
        title_text = f"{obj.get('title','Untitled')}{icon}"
        Label(cf, text=title_text, font=("Arial",16,"bold"), bg="#fff", fg="#0f172a").pack(anchor="w", padx=20)
        Label(cf,text=obj.get("content",""),font=("Arial",11),bg="#fff",fg="#1f2937",justify="left",wraplength=620).pack(anchor="w",padx=20,pady=(4,12))
        dt = datetime.datetime.fromisoformat(obj.get("updated")) if obj.get("updated") else None
        Label(cf,text=(dt.strftime("Updated %d/%m/%Y, %H:%M:%S") if dt else f"Created {obj['date']} {obj['time']}"),
              font=("Arial",10),bg="#fff",fg="#64748b").pack(anchor="w",padx=20,pady=(0,18))
        for w in cf.winfo_children()+trow.winfo_children():
            w.bind("<Double-Button-1>",lambda e,o=obj: open_item(o))

    def refresh(_=None):
        for w in cards.winfo_children(): w.destroy()
        if not notes:
            Label(cards, text="No notes yet. Click 'New Note' to get started.",
                  font=("Arial",12),bg="#fff",fg="#64748b").pack(pady=60)
        else:
            for i,obj in sorted(enumerate(notes), key=lambda x: x[1].get("updated",""), reverse=True):
                render_card(i,obj)

    ns.bind("<<NotesUpdated>>",refresh)
    refresh()
# ==========================
# End Note System
# ==========================

# -----------------------------------------
#  FUNCTION: Create the table
# -----------------------------------------
def create_table():
    """Creates the calendar grid with days and time slots (reuses existing data if available)"""
    for col, day in enumerate(days):
        header = Label(calendar_frame, text=day, font=("Arial", 11), borderwidth=1,
                       relief="solid", width=15, bg="lightblue")
        header.grid(row=0, column=col, sticky="nsew")

    for row, time in enumerate(times, start=1):
        # Time labels
        time_label = Label(calendar_frame, text=time, font=("Arial", 11),
                           borderwidth=1, relief="solid", width=15)
        time_label.grid(row=row, column=0, sticky="nsew")

        for col in range(1, len(days)):
            cell = Label(calendar_frame, text="", font=("Arial", 11),
                         borderwidth=1, relief="solid", width=15)
            cell.grid(row=row, column=col, sticky="nsew")

            # Bind click actions
            cell.bind("<Button-1>", lambda e, r=row, c=col: click_on_cell(r, c))
            cell.bind("<Button-3>", lambda e, r=row, c=col: start_pomodoro_from_cell(r, c))

            cells[(row, col)] = cell

    # Ensures that sessions remain saved when a different menu is used.
    for key, info in sessions.items():
        row, col = key
        cell = cells.get(key)
        if cell: # only top cell of a session should show text
            course = info["course"]
            color = info["color"]

            # Find the cell directly above the current cell
            above_key = (row - 1, col)

            # Check if the cell above exists and belongs to the same course
            if above_key in sessions:
                if sessions[above_key]["course"] == course:
                    # The cell above is part of the same session
                    is_top_cell = False
                else:
                    # The cell above is a different course
                    is_top_cell = True
            else:
                # There is no session in the cell above
                is_top_cell = True

            # Update the current cell
            if is_top_cell:
                # Show the course name only in the top cell of the session
                cell.config(text=course, bg=color)
            else:
                # Leave the text empty in lower cells, but keep the background color
                cell.config(text="", bg=color)

    # Make grid responsive
    for d in range(len(days)):
        calendar_frame.grid_columnconfigure(d, weight=1)
    for t in range(len(times) + 1):
        calendar_frame.grid_rowconfigure(t, weight=1)

# -----------------------------------------
#  FUNCTION: Show Instructions
# -----------------------------------------
def show_instructions():
    """Displays the instructions screen in the main frame."""
    # Clear the main frame
    for widget in main_frame.winfo_children():
        widget.destroy()

    header = Label(main_frame, text="Welcome to the Study Planner!", font=("Arial", 14, "bold"))
    header.pack(pady=5)

    instructions_text = (
        "- Add new courses via the 'Manage Courses' option in the Study Planner menu.\n"
        "- Click on calendar cells to add a study session.\n"
        "- Left-click on an existing session to edit or delete it.\n"
        "- Right-click on a session to start a Pomodoro timer for that course.\n\n"
        "Additional features:\n"
        "- Add notes, create flashcards and quizzes, or start the Pomodoro timer from the menu.\n"
        "- Track scheduled hours per course in the Course Hour Tracker."
    )

    text_box = Text(main_frame, wrap="word", font=("Arial", 11), padx=15, pady=10)
    text_box.insert("1.0", instructions_text)
    text_box.config(state="disabled")
    text_box.pack(fill="both", expand=True, padx=10, pady=5)

    Button(main_frame, text="Open Study Planner", command=study_planner, bg="lightblue").pack(pady=10)

# -----------------------------------------
#  FUNCTION: Show Study Planner
# -----------------------------------------
def study_planner():
    """Shows the planner"""
    global calendar_frame

    # Clear the main frame
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Header
    header_frame = Frame(main_frame)
    header_frame.pack(side="top", fill="x")

    label_planner = Label(header_frame, text="Study Planner", font=("Arial", 11, "bold"))
    label_planner.pack(side="left", padx=10, pady=5)

    # Button to clear the planner
    Button(header_frame, text="Clear Planner", command=clear_planner, bg="lightcoral").pack(side="right", padx=10, pady=5)

    # Calendar container
    calendar_frame = Frame(main_frame)
    calendar_frame.pack(fill="both", expand=True)

    create_table()

# -----------------------------------------
#  FUNCTION: Clear the planner
# -----------------------------------------
def clear_planner():
    """Completely clears the current planner"""
    confirm = messagebox.askyesno("Clear Planner", "Are you sure you want to clear all sessions?")
    if not confirm:
        return

    # Reset dictionaries
    sessions.clear()
    for key, cell in cells.items():
        if key[1] != 0:  # deletes the cells but skips time labels
            cell.config(text="", bg="SystemButtonFace")

    messagebox.showinfo("Planner Cleared", "All study sessions have been cleared.")

# -----------------------------------------
#  FUNCTION: Choose Course and Add Session
# -----------------------------------------
# --- Handle clicks on cells ---
def click_on_cell(row, col):
    """Handles what happens when a user clicks on a calendar cell."""
    cell_key = (row, col)

    # --- Case 1: Editing or deleting an existing session ---
    if cell_key in sessions:
        choice = edit_or_delete_study_session(row, col)

        # If user chooses to edit
        if choice == "edit":
            if not courses:
                messagebox.showerror("Error", "No courses available. Add courses first in Manage Courses.")
                return

            # Ask for the course
            course_name = ask_for_course()
            if not course_name:
                return

            # Ask the study length
            session_length = study_length(row)
            if session_length is None:
                return

            color_choice(course_name, row, col, session_length)

        # If user chooses to delete
        elif choice == "delete":
            course_to_delete = sessions[cell_key]["course"]
            for key in list(sessions.keys()):
                if sessions[key]["course"] == course_to_delete and key[1] == col:
                    sessions.pop(key)
                    cells[key].config(text="", bg="SystemButtonFace")
        return

    # --- Case 2: Adding a new session ---
    if not courses:
        messagebox.showerror("Error", "No courses available. Add courses first in Manage Courses.")
        return

    # Check if this cell is already occupied or colored
    cell = cells.get((row, col))
    if (row, col) in sessions or (cell and cell.cget("bg") != "SystemButtonFace"):
        messagebox.showerror("Error", "This time slot is already taken. Please choose another.")
        return

    # Ask for the course
    course_name = ask_for_course()
    if not course_name:
        return

    session_length = study_length(row)
    if session_length is None:
        return

    color_choice(course_name, row, col, session_length)

# -----------------------------------------
#  FUNCTION: Ask for Course
# -----------------------------------------
def ask_for_course():
    """
    Opens a small pop-up window that allows the user to choose a course.
    Returns the name of the course that the user selects.
    """

    # Create a new pop-up window on top of the main application
    course_selection = Toplevel(root_window)  # Toplevel creates a new window
    course_selection.title("Select Course")   # Set the title of the window
    course_selection.geometry("300x200")      # Set the size of the window (width x height)

    Label(course_selection, text="Select course for this session:").pack(pady=10)

    # Create a variable to store which course the user selects
    selected_course = {"name": None}

    # Function to run when the user clicks on a course button
    def select_course(name):
        """
        This function is called when the user clicks a course button.
        It stores the chosen course in 'selected_course' and closes the pop-up window.
        """
        selected_course["name"] = name       # Save the selected course name
        course_selection.destroy()           # Close the pop-up window

    # Create a button for each course in the courses list
    for course_name in courses.keys():
        # When a button is clicked, call 'select_course' with the course's name
        Button(course_selection, text=course_name, width=20,
               command=lambda n=course_name: select_course(n)).pack(pady=2)

    # Pause the program here until the user closes the pop-up
    course_selection.wait_window()

    # Retrieve the course the user selected
    course = selected_course["name"]

    # If the user didn't select any course, return None
    if not course:
        return

    # Otherwise, return the name of the selected course
    return selected_course["name"]


# -----------------------------------------
#  FUNCTION: Edit or delete a study session
# -----------------------------------------
def edit_or_delete_study_session(row=None, col=None):
    """Opens a small window to let user edit, delete, or add a note for a scheduled study session"""
    popup = Toplevel(root_window)
    popup.title("Choose Action")
    popup.minsize(width=220, height=160)
    choice = {"value": None}

    def set_choice(option):
        choice["value"] = option
        popup.destroy()

    Label(popup, text="Select what you want to do:").pack(pady=10)
    Button(popup, text="Edit", width=15, command=lambda: set_choice("edit")).pack(pady=3)
    Button(popup, text="Delete", width=15, command=lambda: set_choice("delete")).pack(pady=3)
    Button(popup, text="Add Note", width=15, command=lambda: set_choice("note")).pack(pady=3)
    Button(popup, text="Cancel", width=15, command=lambda: set_choice("cancel")).pack(pady=3)

    popup.wait_window()
    if choice["value"] == "note" and row and col:
        add_note_from_cell(row, col)
    return choice["value"]


# -----------------------------------------
# FUNCTION: Ask for Session Length
# -----------------------------------------
def study_length(row):
    """Asks user for session length (in 30-min blocks)"""
    session_length = simpledialog.askstring("Session Length","Enter length in 30-min blocks (1=30 min, 2=1 hr, etc):",parent=root_window)
    if not session_length or not session_length.isdigit():
        messagebox.showerror("Error", "Invalid session length.")
        return None

    session_length = int(session_length)
    if session_length < 1 or (row-1) + session_length - 1 > len(times):
        messagebox.showerror("Error", "Please enter a valid number (1 or higher).")
        return None
    return session_length

# -----------------------------------------
#  FUNCTION: Fill Cells with Course Info
# -----------------------------------------
def color_choice(course, row, col, session_length):
    """Fills the chosen cells with the course name and color"""
    global color_index
    # Assign a color to the course if not already done
    if course not in course_colors:
        color = colorchooser.askcolor(title=f"Choose color for {course}")[1]
        if not color:
            color = colors[color_index % len(colors)] #If there isnt a color chosen, it is one of the list
        course_colors[course] = color
        color_index += 1
    color = course_colors[course]

    # Fill cells for that session
    for l in range(session_length):
        target_row = row + l
        key = (target_row, col)
        sessions[key] = {"course": course, "color": color}
        cell = cells.get(key)
        if cell:
            is_top_cell = (l == 0)
            cell.config(text=course if is_top_cell else "", bg=color)

# -----------------------------------------
#  FUNCTION: Manage Courses
# -----------------------------------------
def manage_courses():
    """
    Opens a pop-up window that allows the user to add, edit, or delete courses.
    This function updates both the list of courses and the calendar sessions if needed.
    """

    # Create a new pop-up window
    mc_window = Toplevel(root_window)  # Toplevel creates a new window on top of the main app
    mc_window.title("Manage Courses")   # Set the window title
    mc_window.geometry("400x300")       # Set the window size (width x height)

    Label(mc_window, text="Manage Courses", font=("Arial", 12, "bold")).pack(pady=5)

    # Create a frame to hold the list of courses and its scrollbar
    list_frame = Frame(mc_window)
    list_frame.pack(fill="both", expand=True, padx=10, pady=5)

    # Create the listbox and scrollbar that will display all courses
    listbox = Listbox(list_frame)
    listbox.pack(side="left", fill="both", expand=True)

    scrollbar = Scrollbar(list_frame, orient="vertical")
    scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set)  # Link listbox to scrollbar
    scrollbar.config(command=listbox.yview)      # Link scrollbar to listbox

    # Populate the listbox with all existing courses
    for course in courses.keys():
        listbox.insert(END, course)

    # --- Function to add a new course ---
    def add_course():
        # Ask the user for the name of the new course
        course_name = simpledialog.askstring("Add Course", "Enter course name:", parent=mc_window)
        if not course_name:  # If the user cancels or enters nothing
            return
        if course_name in courses:  # Check if the course already exists
            messagebox.showerror("Error", "Course already exists.")
            return

        # Let the user choose a color for the course
        color = colorchooser.askcolor(title=f"Choose color for {course_name}")[1]
        if not color:  # If no color is selected, pick a default color from the list
            global color_index
            color = colors[color_index % len(colors)]

        # Save the course and its color
        courses[course_name] = color
        course_colors[course_name] = color

        # Add the course to the listbox
        listbox.insert(END, course_name)

        # Close the manage courses window
        mc_window.destroy()

    # --- Function to edit an existing course ---
    def edit_course():
        # Check which course the user selected
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No course selected.")
            return

        old_name = listbox.get(selection[0])

        # Ask for the new course name
        new_name = simpledialog.askstring("Edit Course", "Enter new course name:", initialvalue=old_name,
                                          parent=mc_window)
        if not new_name:
            return

        # Ask for a new color or use the old color if none selected
        color = colorchooser.askcolor(title=f"Choose color for {new_name}")[1] or course_colors[old_name]

        # If the name is unchanged, just update the color
        if new_name == old_name:
            course_colors[old_name] = color
            courses[old_name] = color
        else:
            # Remove old entries
            if old_name in courses:
                del courses[old_name]
            if old_name in course_colors:
                del course_colors[old_name]
            # Add the updated one
            courses[new_name] = color
            course_colors[new_name] = color

        # Update all existing sessions in the calendar that use this course
        for key, info in sessions.items():
            if info["course"] == old_name:
                # Update course name and color
                info["course"] = new_name
                info["color"] = color

        # Now update all cells in the calendar
        for key, cell in cells.items():
            if key in sessions:
                session_info = sessions[key]
                # Determine if this is the top cell of the session
                above_key = (key[0] - 1, key[1])
                is_top_cell = True
                if above_key in sessions and sessions[above_key]["course"] == session_info["course"]:
                    is_top_cell = False
                # Update text and background
                cell.config(text=session_info["course"] if is_top_cell else "", bg=session_info["color"])

        # Refresh listbox
        listbox.delete(selection[0])
        listbox.insert(selection[0], new_name)
        messagebox.showinfo("Success", f"Course '{old_name}' updated to '{new_name}'.", parent=mc_window)

    # --- Function to delete a course ---
    def delete_course():
        # Check which course is selected
        selection = listbox.curselection()
        if not selection:
            messagebox.showerror("Error", "No course selected.")
            return

        course_to_delete = listbox.get(selection[0])

        # Ask the user to confirm deletion
        confirm = messagebox.askyesno("Confirm", f"Delete course '{course_to_delete}' and all its sessions?")
        if not confirm:
            return

        # Remove all sessions of this course from the calendar
        for key in list(sessions.keys()):
            if sessions[key]["course"] == course_to_delete:
                sessions.pop(key)
                cells[key].config(text="", bg="SystemButtonFace")  # Reset cell appearance

        # Remove the course from dictionaries
        courses.pop(course_to_delete)
        course_colors.pop(course_to_delete)

        # Remove the course from the listbox
        listbox.delete(selection[0])

        # Close the manage courses window
        mc_window.destroy()

    # Add buttons for Add, Edit, Delete courses
    button_frame = Frame(mc_window)
    button_frame.pack(pady=10)

    Button(button_frame, text="Add", width=10, command=add_course).grid(row=0, column=0, padx=5)
    Button(button_frame, text="Edit", width=10, command=edit_course).grid(row=0, column=1, padx=5)
    Button(button_frame, text="Delete", width=10, command=delete_course).grid(row=0, column=2, padx=5)

# -----------------------------------------
#  FUNCTION: Show Course Hour Tracker
# -----------------------------------------
def course_tracker():
    """
    Shows a summary of how many hours have been scheduled for each course.
    Displays both a table and a visual bar chart.
    Allows the user to manually add study hours.
    """

    # Clear the main window
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Header
    Label(main_frame, text="Course Tracker", font=("Arial", 12, "bold")).pack(pady=5)

    # Create a frame for the table
    table_frame = Frame(main_frame)
    table_frame.pack(padx=10, pady=10)

    # Table headers
    Label(table_frame, text="Course", font=("Arial", 11, "bold"), borderwidth=1, relief="solid", width=20,
          bg="lightblue").grid(row=0, column=0, sticky="nsew")
    Label(table_frame, text="Tracked Hours", font=("Arial", 11, "bold"), borderwidth=1, relief="solid", width=20,
          bg="lightblue").grid(row=0, column=1, sticky="nsew")
    Label(table_frame, text="Hours Left/Overspent", font=("Arial", 11, "bold"), borderwidth=1, relief="solid", width=20,
          bg="lightblue").grid(row=0, column=2, sticky="nsew")

    # Count the total scheduled hours for each course
    max_hours = 14  # Maximum planned hours for a course
    course_hours = {}
    # Add the hours from scheduled sessions in the calendar
    for key, info in sessions.items():
        course = info["course"]
        course_hours[course] = course_hours.get(course, 0) + 0.5  # Each session block = 0.5 hour

    # Add hours tracked via Pomodoro timer
    for course, pomodoro_hours in tracked_hours.items():
        course_hours[course] = course_hours.get(course, 0) + pomodoro_hours

    # Fill the table with course data
    for i, (course, hours) in enumerate(course_hours.items(), start=1):
        hours_left = max_hours - hours
        left_text = f"{hours_left:.1f}h left" if hours_left >= 0 else f"{-hours_left:.1f}h overspent"

        # Display course name, total hours, and hours left/overspent
        Label(table_frame, text=course, width=20, anchor="w").grid(row=i, column=0, sticky="n")
        Label(table_frame, text=f"{hours:.1f}", width=20, anchor="w").grid(row=i, column=1, sticky="w")
        Label(table_frame, text=left_text, width=20, anchor="w").grid(row=i, column=2, sticky="w")

    # Show message if there are no study sessions
    if not course_hours:
        Label(main_frame, text="No study sessions yet.", fg="gray").pack(pady=20)

    # --- Create a visual bar chart ---
    vis_label = Label(main_frame, text="Visualization of Hours per Course", font=("Arial", 11, "bold"))
    vis_label.pack(pady=5)

    canvas = Canvas(main_frame, width=550, height=250, bg="white")
    canvas.pack(pady=10)

    if course_hours:
        bar_width = 40         # Width of each bar
        spacing = 20           # Space between bars
        start_x = 50           # Starting x-coordinate
        max_height = 100       # Maximum bar height representing 14 hours

        sorted_courses = list(course_hours.keys())
        for i, course in enumerate(sorted_courses):
            hours = course_hours[course]
            bar_height = min(hours / max_hours * max_height, max_height)  # Height of bar based on hours
            x0 = start_x + i * (bar_width + spacing)
            y0 = 220 - bar_height
            x1 = x0 + bar_width
            y1 = 220

            # Get the course color
            color = course_colors.get(course, "lightblue")

            # Draw the main bar
            canvas.create_rectangle(x0, y0, x1, y1, fill=color)

            # Draw red overspent bar if hours exceed maximum
            if hours > max_hours:
                overshoot_height = (hours - max_hours) / max_hours * max_height
                canvas.create_rectangle(x0, y0 - overshoot_height, x1, y0, fill="red")

            # Add labels for course name and hours
            canvas.create_text((x0 + x1)/2, y1 + 15, text=course, font=("Arial", 10))
            canvas.create_text((x0 + x1)/2, y0 - 10, text=f"{hours:.1f}h", font=("Arial", 10))

        # Draw a line showing maximum allowed hours
        canvas.create_line(30, 220 - max_height, 550, 220 - max_height, fill="black", dash=(4,2))
        canvas.create_text(25, 220 - max_height, text="14h", anchor="e", font=("Arial", 10))

    # --- Button to manually add study hours ---
    def add_study_hours():
        # Ensure there are courses available
        if not courses:
            messagebox.showerror("Error", "No courses available. Add courses first in Manage Courses.")
            return

        # Ask user which course to add hours to
        course_selection = Toplevel(main_frame)
        course_selection.title("Select Course")
        course_selection.geometry("300x250")
        Label(course_selection, text="Which course do you want to add study hours to?", font=("Arial", 11)).pack(pady=10)

        selected_course_var = {"name": None}

        def select_course(name):
            selected_course_var["name"] = name
            course_selection.destroy()

        for c in courses.keys():
            Button(course_selection, text=c, width=25, command=lambda n=c: select_course(n)).pack(pady=3)

        course_selection.wait_window()
        selected_course = selected_course_var["name"]
        if not selected_course:
            return

        # Ask for number of 30-minute blocks to add
        while True:
            input_hours = simpledialog.askstring("Add Hours",
                                                 f"How many 30-minute blocks do you want to add to '{selected_course}'?\n(1 = 30 min, 2 = 1 hour, etc.)",
                                                 parent=main_frame)
            if input_hours is None:
                return
            if not input_hours.isdigit() or int(input_hours) < 1:
                messagebox.showerror("Error", "Please enter a valid number (1 or higher).")
                continue
            input_hours = int(input_hours)
            break

        # Add the hours to tracked_hours
        tracked_hours[selected_course] = tracked_hours.get(selected_course, 0) + 0.5 * input_hours
        messagebox.showinfo("Success", f"Added {0.5 * input_hours} hours to '{selected_course}'.")

        # Refresh the tracker to show updated values
        course_tracker()

    # Add the button to the main window
    Button(main_frame, text="Add Study Hours", width=20, bg="lightgreen", command=add_study_hours).pack(pady=10)

# -----------------------------------------
#  FUNCTION: Flashcards & Quizzes
# -----------------------------------------
def flashcards():
    messagebox.showinfo("Flashcards", "Flashcards feature will be added soon.", parent=root_window)

def quizzes():
    messagebox.showinfo("Quizzes", "Quizzes feature will be added soon.", parent=root_window)

# -----------------------------------------
#  FUNCTION: Pomodoro Timer
# -----------------------------------------
def pomodoro_timer(selected_course=None, count_hours=True):
    """
    Pomodoro Timer: 25 minutes study / 5 minutes break.
    Tracks hours for each course if selected.
    """

    # Set Pomodoro and break durations
    pomodoro_time = 25  # Minutes
    break_time = 5      # Minutes

    # Ask user to select a course if none is provided
    if not selected_course:
        course_selection = Toplevel(root_window)
        course_selection.title("Select Course")
        course_selection.geometry("300x250")

        Label(course_selection, text="Which course are you studying?", font=("Arial", 11, "bold")).pack(pady=10)

        selected_course_var = {"name": None}

        # Function to save selected course and close popup
        def select_course(name):
            selected_course_var["name"] = name
            course_selection.destroy()

        # Buttons for each course
        for c in courses.keys():
            Button(course_selection, text=c, width=20, command=lambda n=c: select_course(n)).pack(pady=3)

        # Option for general session (not linked to a course)
        Button(course_selection, text="General (no specific course)", width=25,
               command=lambda: select_course("General")).pack(pady=10)

        # Wait until user selects a course
        course_selection.wait_window()
        selected_course = selected_course_var["name"]
        if not selected_course:
            return  # User cancelled selection

    # Clear main window
    for widget in main_frame.winfo_children():
        widget.destroy()

    # Headers
    Label(main_frame, text="Pomodoro Timer", font=("Arial", 14, "bold")).pack(pady=10)
    Label(main_frame, text=f"Course: {selected_course}", font=("Arial", 12)).pack(pady=5)

    # Create a canvas to visualize timer progress
    canvas_size = 200
    timer_canvas = Canvas(main_frame, width=canvas_size, height=canvas_size, highlightthickness=0)
    timer_canvas.pack(pady=20)

    # Background circle
    circle_bg = timer_canvas.create_oval(10, 10, canvas_size - 10, canvas_size - 10, outline="white", width=20)
    # Foreground arc that fills as time passes
    circle_fg = timer_canvas.create_arc(10, 10, canvas_size - 10, canvas_size - 10,
                                        start=90, extent=0, style="arc",
                                        outline="green", width=20)
    # Text inside circle showing countdown
    timer_text = timer_canvas.create_text(canvas_size / 2, canvas_size / 2,
                                          text=f"{pomodoro_time:02}:00", font=("Arial", 24, "bold"))

    # Status label
    status_label = Label(main_frame, text="Status: Ready to start", font=("Arial", 12))
    status_label.pack(pady=10)

    # Internal state variables
    is_running = {"value": False}       # Is the timer currently running?
    is_study_time = {"value": True}     # Are we in a study period or break?
    remaining_seconds = {"value": pomodoro_time * 60}  # Countdown in seconds

    # Function to format seconds as MM:SS
    def format_time(seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins:02}:{secs:02}"

    # Timer countdown
    def update_timer():
        if remaining_seconds["value"] > 0 and is_running["value"]:
            # Reduce time by 1 second
            remaining_seconds["value"] -= 1
            total_seconds = pomodoro_time * 60 if is_study_time["value"] else break_time * 60
            progress = (total_seconds - remaining_seconds["value"]) / total_seconds * 360
            color = "green" if is_study_time["value"] else "red"
            timer_canvas.itemconfig(timer_text, text=format_time(remaining_seconds["value"]))
            timer_canvas.itemconfig(circle_fg, extent=progress, outline=color)
            # Call this function again after 1 second
            main_frame.after(1000, update_timer)
        elif remaining_seconds["value"] == 0:
            # Time is up
            is_running["value"] = False
            if is_study_time["value"]:
                try: winsound.Beep(600, 1600)
                except: pass
                # Ask to add 0.5 hours if counting hours and not a general session
                if count_hours and selected_course != "General":
                    add_time = messagebox.askyesno(
                        "Pomodoro Finished",
                        f"Study session finished!\nDo you want to add 0.5 hour to '{selected_course}'?"
                    )
                    if add_time:
                        tracked_hours[selected_course] = tracked_hours.get(selected_course, 0) + 0.5
                else:
                    messagebox.showinfo("Pomodoro", f"Study session for '{selected_course}' finished.")

                # Start break
                is_study_time["value"] = False
                remaining_seconds["value"] = break_time * 60
                status_label.config(text="Status: Break time")
                update_timer()
                messagebox.showinfo("Break", "Break started!")

            else:
                try: winsound.Beep(600, 1600)
                except: pass
                messagebox.showinfo("Pomodoro", "Break is over! Back to studying.")
                is_study_time["value"] = True
                remaining_seconds["value"] = pomodoro_time * 60
                status_label.config(text="Status: Study time")
                update_timer()

    # Timer control buttons
    def start_timer():
        if not is_running["value"]:
            is_running["value"] = True
            status_label.config(text="Status: Running")
            update_timer()

    def stop_timer():
        is_running["value"] = False
        status_label.config(text="Status: Stopped")

    def reset_timer():
        is_running["value"] = False
        remaining_seconds["value"] = pomodoro_time * 60 if is_study_time["value"] else break_time * 60
        status_label.config(text="Status: Study time" if is_study_time["value"] else "Status: Break time")
        timer_canvas.itemconfig(timer_text, text=format_time(remaining_seconds["value"]))
        timer_canvas.itemconfig(circle_fg, extent=0, outline="green")

    # Display buttons
    button_frame = Frame(main_frame)
    button_frame.pack(pady=10)
    Button(button_frame, text="Start", width=10, command=start_timer).grid(row=0, column=0, padx=5)
    Button(button_frame, text="Stop", width=10, command=stop_timer).grid(row=0, column=1, padx=5)
    Button(button_frame, text="Reset", width=10, command=reset_timer).grid(row=0, column=2, padx=5)

# -----------------------------------------
#  FUNCTION: Bind timer and schedule
# -----------------------------------------
def start_pomodoro_from_cell(row, col):
    """Start Pomodoro directly from a study session (right-click)."""
    key = (row, col)

    if key not in sessions:
        messagebox.showinfo("No session", "You can only start a Pomodoro on a scheduled study session.")
        return

    course_name = sessions[key]["course"]
    pomodoro_timer(selected_course=course_name)

# -----------------------------------------
#  MENU BAR
# -----------------------------------------
def setup_menu():
    menubar = Menu(root_window)
    root_window.config(menu=menubar)

    # --- Study Planner Menu ---
    study_menu = Menu(menubar, tearoff=0)
    study_menu.add_command(label="Instructions", command=show_instructions)
    study_menu.add_command(label="Open Planner", command=study_planner)
    menubar.add_cascade(label="Study Planner", menu=study_menu)
    study_menu.add_separator()
    study_menu.add_command(label="Exit", command=root_window.quit)

    # --- Course Hour Tracker Menu ---
    tracker_menu = Menu(menubar, tearoff=0)
    tracker_menu.add_command(label="Open Tracker", command=course_tracker)
    tracker_menu.add_command(label="Manage Courses", command=manage_courses)
    menubar.add_cascade(label="Course Hour Tracker & Manager", menu=tracker_menu)

    # --- Note System Menu ---
    notes_menu = Menu(menubar, tearoff=0)
    notes_menu.add_command(label="Open Notes", command=open_notes_system)
    menubar.add_cascade(label="Note System", menu=notes_menu)

    # --- Flashcards ---
    flash_quiz_menu = Menu(menubar, tearoff=0)
    flash_quiz_menu.add_command(label="Open Flashcards", command=flashcards)
    flash_quiz_menu.add_command(label="Open Quiz", command=quizzes)
    menubar.add_cascade(label="Flashcards & Quizzes", menu=flash_quiz_menu)

    # --- Pomodoro timer ---
    pomodoro_menu = Menu(menubar, tearoff=0)
    pomodoro_menu.add_command(label="Open Pomodoro Timer", command=pomodoro_timer)
    menubar.add_cascade(label="Pomodoro timer", menu=pomodoro_menu)

# -----------------------------------------
#  RUN APP
# -----------------------------------------
setup_menu()
show_instructions()  # Show instructions directly in the main window at startup
root_window.mainloop()



