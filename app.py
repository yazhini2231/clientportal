from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import sqlite3
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
DB_PATH = BASE_DIR / "portal.db"
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "txt", "png", "jpg", "jpeg", "xlsx", "pptx", "zip"}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            client TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'In Progress',
            progress INTEGER NOT NULL DEFAULT 0,
            due_date TEXT NOT NULL DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            assigned_to TEXT NOT NULL DEFAULT 'Team',
            status TEXT NOT NULL DEFAULT 'Pending',
            FOREIGN KEY(project_id) REFERENCES projects(id)
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_name TEXT NOT NULL,
            uploaded_at TEXT NOT NULL
        );
        """)
        count = db.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        if count == 0:
            db.executemany(
                "INSERT INTO projects(name, client, status, progress, due_date) VALUES(?,?,?,?,?)",
                [
                    ("Website Redesign", "GreenLeaf Traders", "In Progress", 65, "2026-10-20"),
                    ("Customer Dashboard", "BrightPath Solutions", "Review", 85, "2026-10-28"),
                    ("Mobile App Prototype", "NorthStar Retail", "Planning", 20, "2026-11-10"),
                ],
            )
            db.executemany(
                "INSERT INTO tasks(project_id, title, assigned_to, status) VALUES(?,?,?,?)",
                [
                    (1, "Confirm homepage layout", "Design Team", "In Progress"),
                    (1, "Prepare responsive pages", "Development Team", "Pending"),
                    (2, "Review dashboard charts", "Client", "Completed"),
                ],
            )
            db.execute(
                "INSERT INTO messages(sender, message, created_at) VALUES(?,?,?)",
                ("Project Team", "Welcome to the client portal! Use this space to track projects and share updates.", datetime.now().strftime("%d %b %Y, %I:%M %p")),
            )

@app.route("/")
def index():
    with get_db() as db:
        projects = db.execute("SELECT * FROM projects ORDER BY id DESC").fetchall()
        tasks = db.execute("""SELECT tasks.*, projects.name AS project_name FROM tasks
                              LEFT JOIN projects ON tasks.project_id = projects.id
                              ORDER BY tasks.id DESC""").fetchall()
        messages = db.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 8").fetchall()
        documents = db.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
        stats = {
            "projects": db.execute("SELECT COUNT(*) FROM projects").fetchone()[0],
            "tasks": db.execute("SELECT COUNT(*) FROM tasks WHERE status != 'Completed'").fetchone()[0],
            "documents": db.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
            "messages": db.execute("SELECT COUNT(*) FROM messages").fetchone()[0],
        }
    return render_template("index.html", projects=projects, tasks=tasks, messages=messages, documents=documents, stats=stats)

@app.route("/projects/add", methods=["POST"])
def add_project():
    name = request.form.get("name", "").strip()
    client = request.form.get("client", "").strip()
    due_date = request.form.get("due_date", "").strip()
    if not name or not client:
        flash("Please enter both project name and client name.", "error")
    else:
        with get_db() as db:
            db.execute("INSERT INTO projects(name, client, due_date) VALUES(?,?,?)", (name, client, due_date))
        flash("Project added successfully.", "success")
    return redirect(url_for("index"))

@app.route("/tasks/add", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    project_id = request.form.get("project_id") or None
    assigned_to = request.form.get("assigned_to", "Team").strip() or "Team"
    if not title:
        flash("Task title is required.", "error")
    else:
        with get_db() as db:
            db.execute("INSERT INTO tasks(project_id, title, assigned_to) VALUES(?,?,?)", (project_id, title, assigned_to))
        flash("Task added successfully.", "success")
    return redirect(url_for("index"))

@app.route("/tasks/<int:task_id>/status", methods=["POST"])
def update_task(task_id):
    status = request.form.get("status", "Pending")
    if status not in {"Pending", "In Progress", "Completed"}:
        status = "Pending"
    with get_db() as db:
        db.execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))
    flash("Task status updated.", "success")
    return redirect(url_for("index"))

@app.route("/messages/add", methods=["POST"])
def add_message():
    sender = request.form.get("sender", "").strip() or "Client"
    message = request.form.get("message", "").strip()
    if not message:
        flash("Please type a message before sending.", "error")
    else:
        with get_db() as db:
            db.execute("INSERT INTO messages(sender, message, created_at) VALUES(?,?,?)",
                       (sender, message, datetime.now().strftime("%d %b %Y, %I:%M %p")))
        flash("Message posted.", "success")
    return redirect(url_for("index"))

@app.route("/documents/upload", methods=["POST"])
def upload_document():
    file = request.files.get("document")
    if not file or not file.filename:
        flash("Choose a file to upload.", "error")
        return redirect(url_for("index"))
    original = file.filename
    safe_name = secure_filename(original)
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in ALLOWED_EXTENSIONS:
        flash("File type not allowed. Upload PDF, Office, image, TXT or ZIP files.", "error")
        return redirect(url_for("index"))
    stored_name = f"{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"
    file.save(UPLOAD_DIR / stored_name)
    with get_db() as db:
        db.execute("INSERT INTO documents(filename, original_name, uploaded_at) VALUES(?,?,?)",
                   (stored_name, original, datetime.now().strftime("%d %b %Y, %I:%M %p")))
    flash("Document uploaded successfully.", "success")
    return redirect(url_for("index"))

@app.route("/documents/<path:filename>")
def download_document(filename):
    return send_from_directory(UPLOAD_DIR, filename, as_attachment=True)

if __name__ == "__main__":
    init_db()
    print("Client Portal running at http://127.0.0.1:5000")
    app.run(debug=True)
