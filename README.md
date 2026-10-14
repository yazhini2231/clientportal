# Client Portal & Project Management

A beginner-friendly Python Flask web app for client project tracking, task management, document sharing, and communication. Data is stored locally in SQLite.

## Features
- Project list with client, status, progress, and due date
- Add new projects
- Create tasks, assign them, and update task status
- Upload and download shared documents
- Post messages in a shared communication feed
- Dashboard summary cards
- SQLite database created automatically with sample data

## Requirements
- Python 3.10 or newer
- Internet only for the first-time Flask installation

## Run on Windows (PowerShell)
1. Extract the ZIP folder.
2. Open the extracted `Client_Portal_Project` folder in VS Code.
3. Open Terminal in VS Code.
4. Run these commands:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, run this instead (no activation needed):

```powershell
py -m pip install -r requirements.txt
py app.py
```

5. Open this address in your browser: `http://127.0.0.1:5000`

Press `Ctrl + C` in the terminal to stop the server.

## Project structure
- `app.py` - Flask routes and application logic
- `templates/index.html` - dashboard UI
- `static/style.css` - page styling
- `uploads/` - uploaded files are stored here
- `portal.db` - SQLite database, created automatically

## Notes
This is a local demo project, not a production-ready portal. Before public deployment, add authentication/authorization, CSRF protection, stronger configuration, file-size limits, and secure secret management.
