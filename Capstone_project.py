from tkinter import *
from tkinter import simpledialog, messagebox, colorchooser, filedialog, ttk
import winsound
import datetime
import json
import csv
import os

# --- MAIN WINDOW SETUP ---
root_window = Tk()
root_window.title("Weekly Calendar")
root_window.minsize(900, 600)

calendar_frame = Frame(root_window)
calendar_frame.pack(fill="both", expand=True)

days = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
times = []
for h in range(8, 18):
    times.append(f"{h}:00")
    times.append(f"{h}:30")

# --- DATA STRUCTURES ---
cells = {}             # (row,col) -> Label widget
sessions = {}          # (row,col) -> {"course":..., "color":...}
courses = {}           # course_name -> color
course_colors = {}     # same as courses (kept for compatibility)
tracked_hours = {}     # course_name -> hours (float)
flashcards_by_course = {}  # course_name -> {term:definition}

# --- DEFAULT COURSES ---
default_courses = ["Math", "History", "Biology"]
default_colors = ["lightpink", "lightyellow", "lightgreen"]
for name, color in zip(default_courses, default_colors):
    courses[name] = color
    course_colors[name] = color

colors = ["lightgray", "lightcoral", "lightcyan", "yellow", "green", "pink"]
color_index = 0

main_frame = Frame(root_window)
main_frame.pack(fill="both", expand=True)

# ==========================
# NOTE SYSTEM (simple version)
# ==========================
notes = []  # list of note dicts
NOTE_ICON = "📝"

def save_notes_json():
    if not notes:
        messagebox.showwarning("No Notes", "There are no notes to save.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files","*.json")])
    if not file:
        return
    try:
        with open(file, "w", encoding="utf-8") as f:
            json.dump(notes, f, indent=4, ensure_ascii=False)
        messagebox.showinfo("Saved", f"Notes saved to {file}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save notes: {e}")

def save_notes_csv():
    if not notes:
        messagebox.showwarning("No Notes", "There are no notes to save.")
        return
    file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
    if not file:
        return
    keys = ["date","day","time","type","content"]
    try:
        with open(file, "w", newline='', encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for note in notes:
                writer.writerow({k: note.get(k, "") for k in keys})
        messagebox.showinfo("Saved", f"Notes saved to {file}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save notes: {e}")

def launch_note_editor(parent, *, note=None, courses_list=None, title_text="New Note", subtitle_text=None):
    data = note.copy() if note else {}
    editor = Toplevel(parent)
    editor.title(title_text); editor.transient(parent); editor.grab_set()
    Label(editor, text=title_text, font=("Arial",12,"bold")).pack(pady=(8,4))
    if subtitle_text:
        Label(editor, text=subtitle_text, font=("Arial",10)).pack(pady=(0,6))
    opts = ["General"] + [c for c in (courses_list or []) if c!="General"]
    if data.get("course") and data["course"] not in opts:
        opts.append(data["course"])
    course_var = StringVar(value=data.get("course") or "General")
    frame_course = Frame(editor); frame_course.pack(fill="x", padx=12, pady=4)
    Label(frame_course, text="Course:").pack(side="left")
    cb = ttk.Combobox(frame_course, values=opts, textvariable=course_var, state="readonly")
    cb.pack(side="left", fill="x", expand=True, padx=(6,0))
    title_entry = Entry(editor); title_entry.pack(fill="x", padx=12, pady=6)
    if data.get("title"): title_entry.insert(0, data["title"])
    Label(editor, text="Description:").pack(anchor="w", padx=12)
    content_txt = Text(editor, wrap="word", height=8); content_txt.pack(fill="both", expand=True, padx=12, pady=(0,6))
    if data.get("content") and data.get("type","text")=="text":
        content_txt.insert("1.0", data["content"])
    attachment_var = StringVar(value=(data.get("content") if data.get("type") in ["file","audio"] else ""))
    attachment_type = StringVar(value=(data.get("type") if data.get("type") in ["file","audio"] else ""))
    def browse_file():
        p = filedialog.askopenfilename()
        if p:
            attachment_var.set(p); attachment_type.set("file")
    def browse_audio():
        p = filedialog.askopenfilename(filetypes=[("Audio Files","*.mp3 *.wav")])
        if p:
            attachment_var.set(p); attachment_type.set("audio")
    af = Frame(editor); af.pack(fill="x", padx=12, pady=(0,6))
    Button(af, text="📁", width=3, command=browse_file).pack(side="left", padx=4)
    Button(af, text="🎤", width=3, command=browse_audio).pack(side="left", padx=4)
    Label(af, textvariable=attachment_var).pack(side="left", padx=6)
    res = {}
    def _save():
        t = title_entry.get().strip()
        desc = content_txt.get("1.0",END).strip()
        attach = attachment_var.get().strip()
        if not t and not desc and not attach:
            messagebox.showerror("Missing Info","Enter title or content.",parent=editor); return
        if attach:
            nt = attachment_type.get() or 'file'
            content_val = attach
        else:
            nt = 'text'
            content_val = desc
        res['value'] = {"title": t, "content": content_val, "course": None if course_var.get()=="General" else course_var.get(), "type": nt}
        editor.destroy()
    bf = Frame(editor); bf.pack(pady=8)
    Button(bf, text="Save", command=_save).pack(side="left", padx=6)
    Button(bf, text="Cancel", command=editor.destroy).pack(side="left", padx=6)
    editor.wait_window()
    return res.get("value")

def add_note_from_cell(row, col):
    vals = launch_note_editor(root_window, courses_list=list(courses.keys()), title_text="New Note",
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
    if vals.get("title"): note["title"] = vals["title"]
    if vals.get("course"): note["course"] = vals["course"]
    notes.append(note)
    messagebox.showinfo("Note Added", f"Note added for {note['day']} at {note['time']}.")
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
        "day": note["day"] if note else now.strftime("%A"),
        "time": note["time"] if note else now.strftime("%H:%M"),
        "type": note["type"] if note else "text",
        "content": vals["content"],
        "updated": now.isoformat()
    }
    if vals.get("title"): new["title"] = vals["title"]
    if vals.get("course"): new["course"] = vals["course"]
    if note_index is None or note is None:
        notes.append(new)
    else:
        notes[note_index] = new
    parent.event_generate("<<NotesUpdated>>")

def open_notes_system():
    ns = Toplevel(root_window); ns.title("Notes"); ns.geometry("720x520")
    ns.configure(bg="#fff")
    hf = Frame(ns,bg="#fff"); hf.pack(fill="x",padx=20,pady=(20,10))
    Label(hf,text="Notes",font=("Arial",20,"bold"),bg="#fff",fg="#0f172a").pack(side="left")
    ttk.Button(hf,text="+ New Note",command=lambda:add_note_from_notes_window(ns)).pack(side="right")
    Label(hf,text=datetime.date.today().strftime("%A, %B %d, %Y"),font=("Arial",11),bg="#fff",fg="#475569").pack(anchor="w",pady=(4,0))
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
    ff = Frame(ns,bg="#fff"); ff.pack(fill="x",padx=20,pady=10)
    ttk.Button(ff,text="Save JSON",command=save_notes_json).pack(side="left",padx=(0,10))
    ttk.Button(ff,text="Save CSV", command=save_notes_csv).pack(side="left",padx=(0,10))
    ttk.Button(ff,text="Close",     command=ns.destroy).pack(side="right")
    def badge_colors(name):
        bg = course_colors.get(name,"#0ea5e9") if name else "#0ea5e9"
        try:
            r,g,b = ns.winfo_rgb(bg)
            bright = (0.299*r+0.587*g+0.114*b)/65535
            fg = "#0f172a" if bright>0.75 else "#fff"
        except:
            fg = "#fff"
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
        icon = ""
        if obj.get("type") == "audio":
            icon = " 🎤"
        elif obj.get("type") == "file":
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

# -----------------------------------------
#  TABLE / CALENDAR
# -----------------------------------------
def create_table():
    for child in calendar_frame.winfo_children():
        child.destroy()
    for col, day in enumerate(days):
        header = Label(calendar_frame, text=day, font=("Arial", 11), borderwidth=1, relief="solid", width=15, bg="lightblue")
        header.grid(row=0, column=col, sticky="nsew")
    for row, time in enumerate(times, start=1):
        time_label = Label(calendar_frame, text=time, font=("Arial", 11), borderwidth=1, relief="solid", width=15)
        time_label.grid(row=row, column=0, sticky="nsew")
        for col in range(1, len(days)):
            cell = Label(calendar_frame, text="", font=("Arial", 11), borderwidth=1, relief="solid", width=15, bg="SystemButtonFace")
            cell.grid(row=row, column=col, sticky="nsew")
            cell.bind("<Button-1>", lambda e, r=row, c=col: click_on_cell(r, c))
            cell.bind("<Button-3>", lambda e, r=row, c=col: start_pomodoro_from_cell(r, c))
            cells[(row, col)] = cell
    for key, info in sessions.items():
        cell = cells.get(key)
        if cell:
            course = info["course"]; color = info["color"]
            above_key = (key[0]-1, key[1])
            if above_key in sessions and sessions[above_key]["course"] == course:
                cell.config(text="", bg=color)
            else:
                cell.config(text=course, bg=color)
    for d in range(len(days)):
        calendar_frame.grid_columnconfigure(d, weight=1)
    for t in range(len(times)+1):
        calendar_frame.grid_rowconfigure(t, weight=1)

def show_instructions():
    for widget in main_frame.winfo_children():
        widget.destroy()
    Label(main_frame, text="Welcome to the Study Planner!", font=("Arial", 14, "bold")).pack(pady=5)
    instructions_text = (
        "- Add new courses via the 'Manage Courses' option in the Study Planner menu.\n"
        "- Click on calendar cells to add a study session.\n"
        "- Left-click on an existing session to edit or delete it (and add notes).\n"
        "- Right-click on a session to start a Pomodoro timer for that course.\n\n"
        "Additional features:\n"
        "- Add notes, create flashcards and quizzes, or start the Pomodoro timer from the menu.\n"
        "- Track scheduled hours per course in the Course Hour Tracker."
    )
    t = Text(main_frame, wrap="word", font=("Arial",11), padx=12, pady=10); t.insert("1.0", instructions_text); t.config(state="disabled"); t.pack(fill="both", expand=True, padx=10, pady=5)
    Button(main_frame, text="Open Study Planner", command=study_planner, bg="lightblue").pack(pady=10)

def study_planner():
    for widget in main_frame.winfo_children():
        widget.destroy()
    hf = Frame(main_frame); hf.pack(side="top", fill="x")
    Label(hf, text="Study Planner", font=("Arial",11,"bold")).pack(side="left", padx=10, pady=6)
    Button(hf, text="Clear Planner", command=clear_planner, bg="lightcoral").pack(side="right", padx=10, pady=6)
    global calendar_frame
    calendar_frame = Frame(main_frame); calendar_frame.pack(fill="both", expand=True)
    create_table()

def clear_planner():
    if not messagebox.askyesno("Clear Planner","Are you sure you want to clear all sessions?"): return
    sessions.clear()
    for key, cell in cells.items():
        cell.config(text="", bg="SystemButtonFace")
    messagebox.showinfo("Planner Cleared", "All study sessions have been cleared.")

def click_on_cell(row, col):
    key = (row, col)
    if key in sessions:
        choice = edit_or_delete_study_session(row, col)
        if choice == "edit":
            if not courses:
                messagebox.showerror("Error","No courses available. Add courses first."); return
            course_name = ask_for_course()
            if not course_name: return
            session_length = study_length(row)
            if session_length is None: return
            # check target blocks for overlap
            for l in range(session_length):
                tkey = (row + l, col)
                if tkey in sessions and sessions[tkey]["course"] != sessions[key]["course"]:
                    messagebox.showerror("Error","Cannot edit: target cells overlap with another course."); return
            color_choice(course_name, row, col, session_length)
        elif choice == "delete":
            course_to_delete = sessions[key]["course"]
            for k in list(sessions.keys()):
                if sessions[k]["course"] == course_to_delete and k[1] == key[1]:
                    sessions.pop(k); cells[k].config(text="", bg="SystemButtonFace")
        return
    # adding new session
    if not courses:
        messagebox.showerror("Error","No courses available. Add courses first."); return
    course_name = ask_for_course()
    if not course_name: return
    session_length = study_length(row)
    if session_length is None: return
    for l in range(session_length):
        tkey = (row + l, col)
        cell = cells.get(tkey)
        if tkey in sessions or (cell and cell.cget("bg") != "SystemButtonFace"):
            messagebox.showerror("Error","This time slot (or part of the requested block) is already taken. Please choose another."); return
    color_choice(course_name, row, col, session_length)

def ask_for_course():
    win = Toplevel(root_window); win.title("Select Course"); win.geometry("300x220")
    Label(win, text="Select course for this session:").pack(pady=10)
    sel = {"name": None}
    def choose(n):
        sel["name"] = n; win.destroy()
    for c in courses.keys():
        Button(win, text=c, width=24, command=lambda n=c: choose(n)).pack(pady=3)
    win.wait_window()
    return sel["name"]

def edit_or_delete_study_session(row=None, col=None):
    popup = Toplevel(root_window); popup.title("Choose Action"); popup.minsize(width=240, height=170)
    choice = {"value": None}
    def set_choice(opt):
        choice["value"] = opt; popup.destroy()
    Label(popup, text="Select what you want to do:").pack(pady=10)
    Button(popup, text="Edit", width=18, command=lambda:set_choice("edit")).pack(pady=3)
    Button(popup, text="Delete", width=18, command=lambda:set_choice("delete")).pack(pady=3)
    Button(popup, text="Add Note", width=18, command=lambda:set_choice("note")).pack(pady=3)
    Button(popup, text="Cancel", width=18, command=lambda:set_choice("cancel")).pack(pady=3)
    popup.wait_window()
    if choice["value"] == "note" and row and col:
        add_note_from_cell(row, col)
    return choice["value"]

def study_length(row):
    s = simpledialog.askstring("Session Length","Enter length in 30-min blocks (1=30 min, 2=1 hr, etc):",parent=root_window)
    if not s or not s.isdigit(): messagebox.showerror("Error","Invalid session length."); return None
    s = int(s)
    if s < 1 or (row-1) + s - 1 > len(times):
        messagebox.showerror("Error","Please enter a valid number (1 or higher)."); return None
    return s

def color_choice(course, row, col, session_length):
    global color_index
    if course not in course_colors:
        color = colorchooser.askcolor(title=f"Choose color for {course}")[1]
        if not color:
            color = colors[color_index % len(colors)]
        course_colors[course] = color
        courses[course] = color
        color_index += 1
    color = course_colors[course]
    for l in range(session_length):
        r = row + l
        key = (r, col)
        sessions[key] = {"course": course, "color": color}
        cell = cells.get(key)
        if cell:
            cell.config(text=course if l==0 else "", bg=color)

def manage_courses():
    mc = Toplevel(root_window); mc.title("Manage Courses"); mc.geometry("420x320")
    Label(mc, text="Manage Courses", font=("Arial",12,"bold")).pack(pady=6)
    lf = Frame(mc); lf.pack(fill="both", expand=True, padx=10, pady=6)
    lb = Listbox(lf); lb.pack(side="left", fill="both", expand=True)
    sb = Scrollbar(lf, orient="vertical", command=lb.yview); sb.pack(side="right", fill="y")
    lb.config(yscrollcommand=sb.set)
    for c in courses.keys(): lb.insert(END, c)
    def add_course():
        name = simpledialog.askstring("Add Course","Enter course name:",parent=mc)
        if not name: return
        if name in courses: messagebox.showerror("Error","Course already exists."); return
        color = colorchooser.askcolor(title=f"Choose color for {name}")[1]
        if not color:
            global color_index
            color = colors[color_index % len(colors)]; color_index += 1
        courses[name] = color; course_colors[name] = color
        lb.insert(END, name); mc.destroy()
    def edit_course():
        sel = lb.curselection()
        if not sel: messagebox.showerror("Error","No course selected."); return
        old = lb.get(sel[0])
        new = simpledialog.askstring("Edit Course","Enter new course name:", initialvalue=old, parent=mc)
        if not new: return
        color = colorchooser.askcolor(title=f"Choose color for {new}")[1] or course_colors.get(old)
        # clear visuals of old course
        keys = [k for k,v in sessions.items() if v["course"]==old]
        for k in keys:
            cell = cells.get(k)
            if cell: cell.config(text="", bg="SystemButtonFace")
        # update data
        if old in courses: del courses[old]
        if old in course_colors: del course_colors[old]
        courses[new] = color; course_colors[new] = color
        for k in keys:
            sessions[k]["course"] = new; sessions[k]["color"] = color
        # repaint
        for k in keys:
            cell = cells.get(k)
            if not cell: continue
            above = (k[0]-1, k[1])
            top = not (above in sessions and sessions[above]["course"]==new)
            cell.config(text=new if top else "", bg=color)
        lb.delete(sel[0]); lb.insert(sel[0], new)
        messagebox.showinfo("Success", f"Course '{old}' updated to '{new}'.", parent=mc)
    def delete_course():
        sel = lb.curselection()
        if not sel: messagebox.showerror("Error","No course selected."); return
        name = lb.get(sel[0])
        if not messagebox.askyesno("Confirm", f"Delete course '{name}' and all its sessions?"): return
        for k in list(sessions.keys()):
            if sessions[k]["course"]==name:
                sessions.pop(k); cell = cells.get(k); 
                if cell: cell.config(text="", bg="SystemButtonFace")
        courses.pop(name, None); course_colors.pop(name, None)
        lb.delete(sel[0]); mc.destroy()
    bf = Frame(mc); bf.pack(pady=8)
    Button(bf, text="Add", width=10, command=add_course).grid(row=0,column=0,padx=6)
    Button(bf, text="Edit", width=10, command=edit_course).grid(row=0,column=1,padx=6)
    Button(bf, text="Delete", width=10, command=delete_course).grid(row=0,column=2,padx=6)

def course_tracker():
    for w in main_frame.winfo_children(): w.destroy()
    Label(main_frame, text="Course Tracker", font=("Arial",12,"bold")).pack(pady=6)
    tf = Frame(main_frame); tf.pack(padx=10,pady=10)
    Label(tf, text="Course", bg="lightblue", width=20).grid(row=0,column=0)
    Label(tf, text="Tracked Hours", bg="lightblue", width=20).grid(row=0,column=1)
    Label(tf, text="Hours Left/Overspent", bg="lightblue", width=20).grid(row=0,column=2)
    maxh = 14; ch = {}
    for k,v in sessions.items():
        course = v["course"]; ch[course] = ch.get(course,0)+0.5
    for c,h in tracked_hours.items(): ch[c] = ch.get(c,0)+h
    if not ch: Label(main_frame, text="No study sessions yet.", fg="gray").pack(pady=20)
    else:
        for i,(course,hours) in enumerate(ch.items(), start=1):
            left = maxh - hours
            left_text = f"{left:.1f}h left" if left>=0 else f"{-left:.1f}h overspent"
            Label(tf, text=course, width=20, anchor="w").grid(row=i,column=0,sticky="n")
            Label(tf, text=f"{hours:.1f}", width=20, anchor="w").grid(row=i,column=1,sticky="w")
            Label(tf, text=left_text, width=20, anchor="w").grid(row=i,column=2,sticky="w")
    Label(main_frame, text="Visualization of Hours per Course", font=("Arial",11,"bold")).pack(pady=6)
    canvas = Canvas(main_frame, width=700, height=250, bg="white"); canvas.pack(pady=8)
    if ch:
        bar_w = 40; spacing=20; start_x=50; maxh_px=100
        courses_order = list(ch.keys())
        for i,course in enumerate(courses_order):
            hours = ch[course]; bh = min(hours/maxh*maxh_px, maxh_px)
            x0 = start_x + i*(bar_w+spacing); y0 = 220-bh; x1 = x0+bar_w; y1=220
            color = course_colors.get(course,"lightblue")
            canvas.create_rectangle(x0,y0,x1,y1, fill=color)
            if hours>maxh:
                overs = (hours-maxh)/maxh*maxh_px
                canvas.create_rectangle(x0,y0-overs,x1,y0,fill="red")
            canvas.create_text((x0+x1)/2, y1+15, text=course, font=("Arial",10))
            canvas.create_text((x0+x1)/2, y0-10, text=f"{hours:.1f}h", font=("Arial",10))
        canvas.create_line(30, 220-maxh_px, 700, 220-maxh_px, fill="black", dash=(4,2))
        canvas.create_text(25, 220-maxh_px, text="14h", anchor="e", font=("Arial",10))
    def add_study_hours():
        if not courses: messagebox.showerror("Error","No courses available."); return
        popup = Toplevel(main_frame); popup.title("Add Hours"); popup.geometry("320x220")
        Label(popup, text="Select course:").pack(pady=8)
        sel = {"name": None}
        for c in courses.keys():
            Button(popup, text=c, width=24, command=lambda n=c: (sel.update({"name":n}), popup.destroy())).pack(pady=3)
        popup.wait_window()
        if not sel["name"]: return
        s = simpledialog.askstring("Add Hours","How many 30-minute blocks to add? (1=30min)", parent=main_frame)
        if not s or not s.isdigit(): messagebox.showerror("Error","Invalid input"); return
        tracked_hours[sel["name"]] = tracked_hours.get(sel["name"],0) + 0.5*int(s)
        messagebox.showinfo("Success", f"Added {0.5*int(s)} hours to '{sel['name']}'.")
        course_tracker()
    Button(main_frame, text="Add Study Hours", width=20, bg="lightgreen", command=add_study_hours).pack(pady=8)

# -----------------------------------------
# FLASHCARDS (from Program 1)
# -----------------------------------------
def manage_flashcards():
    flash_window = Toplevel(root_window)
    flash_window.title("Manage Flashcards")
    flash_window.geometry("500x400")
    Label(flash_window, text="Manage Flashcards", font=("Arial",12,"bold")).pack(pady=5)
    list_frame = Frame(flash_window); list_frame.pack(fill="both", expand=True, padx=10, pady=5)
    listbox = Listbox(list_frame); listbox.pack(side="left", fill="both", expand=True)
    scrollbar = Scrollbar(list_frame, orient="vertical"); scrollbar.pack(side="right", fill="y")
    listbox.config(yscrollcommand=scrollbar.set); scrollbar.config(command=listbox.yview)
    course = None
    def choose_course():
        popup = Toplevel(flash_window); popup.title("Choose Course"); popup.geometry("400x300")
        popup.transient(flash_window); popup.grab_set()
        selected = {"name": None}
        Label(popup, text="Enter a new course or select an existing one:").pack(pady=10)
        entry = Entry(popup); entry.pack(pady=5)
        list_frame2 = Frame(popup); list_frame2.pack(fill="both", expand=True, padx=10, pady=5)
        list_courses = Listbox(list_frame2); list_courses.pack(side="left", fill="both", expand=True)
        scrollbar2 = Scrollbar(list_frame2, orient="vertical", command=list_courses.yview); scrollbar2.pack(side="right", fill="y")
        list_courses.config(yscrollcommand=scrollbar2.set)
        for name in flashcards_by_course.keys(): list_courses.insert(END, name)
        def confirm():
            name = entry.get().strip()
            if not name:
                sel = list_courses.curselection()
                if sel:
                    name = list_courses.get(sel[0])
                else:
                    messagebox.showerror("Error", "Please enter a course name.")
                    return
            selected["name"] = name
            if selected["name"] not in flashcards_by_course:
                flashcards_by_course[selected["name"]] = {}
            popup.destroy()
        def cancel():
            selected["name"] = None; popup.destroy()
        btn_frame = Frame(popup); btn_frame.pack(pady=10)
        Button(btn_frame, text="Confirm", width=10, command=confirm).pack(side="left", padx=5)
        Button(btn_frame, text="Cancel", width=10, command=cancel).pack(side="left", padx=5)
        popup.wait_window()
        return selected["name"]
    def refresh_list():
        listbox.delete(0, END)
        if course:
            for term in flashcards_by_course[course].keys():
                listbox.insert(END, term)
    def switch_course():
        nonlocal course
        course = choose_course()
        if course:
            refresh_list()
    def add_flashcard():
        nonlocal course
        if not course:
            messagebox.showerror("Error", "No course selected.")
            return
        term = simpledialog.askstring("Add Flashcard", "Enter term:", parent=flash_window)
        if not term:
            return
        if term in flashcards_by_course[course]:
            messagebox.showerror("Error", "Term already exists.")
            return
        definition = simpledialog.askstring("Add Flashcard", "Enter definition:", parent=flash_window)
        if definition is None:
            return
        flashcards_by_course[course][term] = definition
        refresh_list()
    def import_from_csv():
        if not course:
            messagebox.showerror("Error", "No course selected.")
            return
        path = filedialog.askopenfilename(title="Open CSV", filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        with open(path, newline='', encoding="utf-8") as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) >= 2:
                    term, definition = row[0], row[1]
                    flashcards_by_course[course][term] = definition
        refresh_list()
        messagebox.showinfo("Success", f"Flashcards successfully imported for {course}.")
    def edit_flashcard():
        if not course:
            messagebox.showerror("Error", "No course selected.")
            return
        sel = listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "No flashcard selected.")
            return
        term = listbox.get(sel[0])
        new_definition = simpledialog.askstring("Edit definition", "Enter new definition:", initialvalue=flashcards_by_course[course][term], parent=flash_window)
        if new_definition is not None:
            flashcards_by_course[course][term] = new_definition
            refresh_list()
    def delete_flashcard():
        if not course:
            messagebox.showerror("Error", "No course selected.")
            return
        sel = listbox.curselection()
        if not sel:
            messagebox.showerror("Error", "No flashcard selected.")
            return
        term = listbox.get(sel[0])
        if messagebox.askyesno("Delete", f"Delete flashcard '{term}'?"):
            flashcards_by_course[course].pop(term)
            refresh_list()
    btn_frame = Frame(flash_window); btn_frame.pack(pady=10)
    Button(btn_frame, text="Switch Course", command=switch_course).grid(row=0, column=0, padx=5)
    Button(btn_frame, text="Add", width=10, command=add_flashcard).grid(row=0, column=1, padx=5)
    Button(btn_frame, text="Edit", width=10, command=edit_flashcard).grid(row=0, column=2, padx=5)
    Button(btn_frame, text="Delete", width=10, command=delete_flashcard).grid(row=0, column=3, padx=5)
    Button(btn_frame, text="Import CSV", width=10, command=import_from_csv).grid(row=0, column=4, padx=5)
    course = choose_course()
    if not course:
        flash_window.destroy()
        return
    refresh_list()

def start_quiz():
    quiz_window = Toplevel(root_window); quiz_window.title("Flashcard Quiz"); quiz_window.geometry("700x300")
    if not flashcards_by_course:
        messagebox.showerror("Error", "No flashcards available, please add flashcards to start quiz.")
        quiz_window.destroy()
        return
    course_popup = Toplevel(root_window); course_popup.title("Select Course"); course_popup.geometry("400x300")
    Label(course_popup, text="Select a course to start quiz:").pack(pady=10)
    listbox = Listbox(course_popup); listbox.pack(fill="both", expand=True, padx=10, pady=5)
    for c in flashcards_by_course:
        listbox.insert(END, c)
    selected_course = {"name": None}
    def confirm_course():
        sel = listbox.curselection()
        if sel:
            selected_course["name"] = listbox.get(sel[0]); course_popup.destroy()
        else:
            messagebox.showerror("Error", "Please select a course.")
    Button(course_popup, text="Start Quiz", command=confirm_course).pack(pady=10)
    course_popup.wait_window()
    course = selected_course["name"]
    if not course or course not in flashcards_by_course or not flashcards_by_course[course]:
        messagebox.showerror("Error", "No flashcards for this course."); return
    terms_dict = flashcards_by_course[course]; terms = list(terms_dict.keys())
    current_flash_index = 0; correct_answers = 0; incorrect_answers = 0
    card_marked = {term: False for term in terms}; total = len(terms)
    term_label = Label(quiz_window, text="", font=("Arial",14,"bold")); term_label.pack(pady=20)
    definition_label = Label(quiz_window, text="", font=("Arial",14,"bold")); definition_label.pack(pady=10)
    def show_next_card():
        nonlocal current_flash_index
        if current_flash_index < total:
            term = terms[current_flash_index]; term_label.configure(text=term); definition_label.configure(text="")
        else:
            messagebox.showinfo("Quiz finished.", f"You reviewed {total} flashcards \\nCorrect Answers: {correct_answers} \\nIncorrect/Skipped Answers: {incorrect_answers}.")
            quiz_window.destroy()
    def show_answer():
        term = terms[current_flash_index]; definition_label.configure(text=terms_dict[term])
    def next_card():
        nonlocal current_flash_index, incorrect_answers
        term = terms[current_flash_index]
        if not card_marked[term]:
            incorrect_answers += 1; card_marked[term] = True
        current_flash_index += 1; show_next_card()
    def mark_correct():
        nonlocal correct_answers, current_flash_index
        term = terms[current_flash_index]
        if not card_marked[term]:
            correct_answers += 1; card_marked[term] = True
        next_card()
    def mark_incorrect():
        nonlocal incorrect_answers, current_flash_index
        term = terms[current_flash_index]
        if not card_marked[term]:
            incorrect_answers += 1; card_marked[term] = True
        next_card()
    def stop_quiz():
        messagebox.showinfo("Quiz finished", f"You reviewed {total} flashcards \\nCorrect answers: {correct_answers} \\nIncorrect/Skipped answers: {incorrect_answers}.")
        quiz_window.destroy()
    btn_frame = Frame(quiz_window); btn_frame.pack(pady=10)
    Button(btn_frame, text="I knew it", width=12, command=mark_correct).grid(row=0, column=0, padx=10)
    Button(btn_frame, text="I didn't know it", width=12, command=mark_incorrect).grid(row=0, column=1, padx=10)
    nav_frame = Frame(quiz_window); nav_frame.pack(pady=10)
    Button(nav_frame, text="Show Answer", width=12, command=show_answer).grid(row=0, column=0, padx=10)
    Button(nav_frame, text="Next", width=12, command=next_card).grid(row=0, column=1, padx=10)
    Button(nav_frame, text="Stop Quiz", width=12, command=stop_quiz).grid(row=0, column=2, padx=10)
    show_next_card()

# -----------------------------------------
# Pomodoro Timer (simple)
# -----------------------------------------
def pomodoro_timer(selected_course=None, count_hours=True):
    pomodoro_time = 25
    break_time = 5
    if not selected_course:
        sel_win = Toplevel(root_window); sel_win.title("Select Course"); sel_win.geometry("300x250")
        Label(sel_win, text="Which course are you studying?", font=("Arial",11,"bold")).pack(pady=10)
        sel = {"name": None}
        for c in courses.keys():
            Button(sel_win, text=c, width=20, command=lambda n=c: (sel.update({"name":n}), sel_win.destroy())).pack(pady=3)
        Button(sel_win, text="General (no specific course)", width=25, command=lambda: (sel.update({"name":"General"}), sel_win.destroy())).pack(pady=10)
        sel_win.wait_window()
        selected_course = sel.get("name")
        if not selected_course: return
    for w in main_frame.winfo_children(): w.destroy()
    Label(main_frame, text="Pomodoro Timer", font=("Arial",14,"bold")).pack(pady=10)
    Label(main_frame, text=f"Course: {selected_course}", font=("Arial",12)).pack(pady=6)
    canvas_size = 200
    timer_canvas = Canvas(main_frame, width=canvas_size, height=canvas_size, highlightthickness=0); timer_canvas.pack(pady=12)
    circle_bg = timer_canvas.create_oval(10,10,canvas_size-10,canvas_size-10, outline="white", width=20)
    circle_fg = timer_canvas.create_arc(10,10,canvas_size-10,canvas_size-10, start=90, extent=0, style="arc", outline="green", width=20)
    timer_text = timer_canvas.create_text(canvas_size/2, canvas_size/2, text=f"{pomodoro_time:02}:00", font=("Arial",24,"bold"))
    status_label = Label(main_frame, text="Status: Ready to start", font=("Arial",12)); status_label.pack(pady=8)
    is_running = {"value": False}; is_study_time = {"value": True}; remaining_seconds = {"value": pomodoro_time*60}
    def format_time(sec):
        m = sec//60; s = sec%60; return f"{m:02}:{s:02}"
    def update_timer():
        if remaining_seconds["value"]>0 and is_running["value"]:
            remaining_seconds["value"] -= 1
            total = pomodoro_time*60 if is_study_time["value"] else break_time*60
            progress = (total-remaining_seconds["value"]) / total * 360
            color = "green" if is_study_time["value"] else "red"
            timer_canvas.itemconfig(timer_text, text=format_time(remaining_seconds["value"]))
            timer_canvas.itemconfig(circle_fg, extent=progress, outline=color)
            main_frame.after(1000, update_timer)
        elif remaining_seconds["value"]==0:
            is_running["value"] = False
            try: winsound.Beep(600,1600)
            except: pass
            if is_study_time["value"]:
                if count_hours and selected_course != "General":
                    if messagebox.askyesno("Pomodoro Finished", f"Study session finished!\\nDo you want to add 0.5 hour to '{selected_course}'?"):
                        tracked_hours[selected_course] = tracked_hours.get(selected_course,0) + 0.5
                is_study_time["value"] = False; remaining_seconds["value"] = break_time*60; status_label.config(text="Status: Break time"); update_timer()
            else:
                is_study_time["value"] = True; remaining_seconds["value"] = pomodoro_time*60; status_label.config(text="Status: Study time"); update_timer()
    def start_timer(): is_running["value"] = True; status_label.config(text="Status: Running"); update_timer()
    def stop_timer(): is_running["value"] = False; status_label.config(text="Status: Stopped")
    def reset_timer(): is_running["value"] = False; remaining_seconds["value"] = pomodoro_time*60 if is_study_time["value"] else break_time*60; timer_canvas.itemconfig(timer_text, text=format_time(remaining_seconds["value"])); timer_canvas.itemconfig(circle_fg, extent=0, outline="green")
    bf = Frame(main_frame); bf.pack(pady=8)
    Button(bf, text="Start", width=10, command=start_timer).grid(row=0,column=0,padx=6)
    Button(bf, text="Stop", width=10, command=stop_timer).grid(row=0,column=1,padx=6)
    Button(bf, text="Reset", width=10, command=reset_timer).grid(row=0,column=2,padx=6)

def start_pomodoro_from_cell(row, col):
    key = (row, col)
    if key not in sessions:
        messagebox.showinfo("No session", "You can only start a Pomodoro on a scheduled study session."); return
    pomodoro_timer(selected_course=sessions[key]["course"])

# -----------------------------------------
# MENU
# -----------------------------------------
def setup_menu():
    menubar = Menu(root_window); root_window.config(menu=menubar)
    study_menu = Menu(menubar, tearoff=0)
    study_menu.add_command(label="Instructions", command=show_instructions)
    study_menu.add_command(label="Open Planner", command=study_planner)
    study_menu.add_separator(); study_menu.add_command(label="Exit", command=root_window.quit)
    menubar.add_cascade(label="Study Planner", menu=study_menu)
    tracker_menu = Menu(menubar, tearoff=0)
    tracker_menu.add_command(label="Open Tracker", command=course_tracker)
    tracker_menu.add_command(label="Manage Courses", command=manage_courses)
    menubar.add_cascade(label="Course Hour Tracker & Manager", menu=tracker_menu)
    notes_menu = Menu(menubar, tearoff=0)
    notes_menu.add_command(label="Open Notes", command=open_notes_system)
    menubar.add_cascade(label="Note System", menu=notes_menu)
    flash_menu = Menu(menubar, tearoff=0)
    flash_menu.add_command(label="Open Flashcards", command=manage_flashcards)
    flash_menu.add_command(label="Open Quiz", command=start_quiz)
    menubar.add_cascade(label="Flashcards & Quizzes", menu=flash_menu)
    pom_menu = Menu(menubar, tearoff=0)
    pom_menu.add_command(label="Open Pomodoro Timer", command=pomodoro_timer)
    menubar.add_cascade(label="Pomodoro timer", menu=pom_menu)

# -----------------------------------------
# RUN
# -----------------------------------------
if __name__ == "__main__":
    setup_menu()
    show_instructions()
    root_window.mainloop()
