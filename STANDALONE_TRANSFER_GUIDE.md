# Standalone Transfer & Setup Guide
## Flexi Training Management System

This project is now fully self-contained as a **Standalone Web Application**. It does NOT require Node.js or `npm` on the target machine.

---

### How it Works
1. The React frontend is pre-built into static assets in the `dist/` directory.
2. The Python Flask server serves both the backend API (`/api/*`) and the frontend UI (`http://localhost:5001`).
3. Running the launcher opens your default web browser to `http://localhost:5001` like a native software application.

---

### Method 1: Transferring to a Linux Desktop (Single-Click Launch)
1. **Copy Folder**: Copy the entire `Flexi-4.0` folder (including `.venv` and `dist`) to the target desktop.
2. **Double-Click Shortcut**:
   - Double-click `Start_Flexi_Training.desktop` or run `./start.sh` in the terminal.
   - The application will launch and automatically open in your web browser.

---

### Method 2: Transferring to a Windows Desktop
1. **Copy Folder**: Copy the `Flexi-4.0` folder to the target Windows computer.
2. **Double-Click Launcher**:
   - Double-click `start.bat`.
   - The server will start and open your web browser automatically at `http://localhost:5001`.

---

### Offline Python Package Bundling (If Python dependencies are needed on a restricted offline machine)
If the target machine has Python 3 installed but no internet connection to download pip packages, you can pre-download all package wheels into a `wheels/` folder before transferring:

```bash
# On a machine with internet access:
pip download -r requirements.txt -d wheels/

# On the restricted destination machine:
pip install --no-index --find-links=wheels/ -r requirements.txt
```

---

### Files Included for Portable Deployment:
- `start.sh`: Executable startup script for Linux
- `start.bat`: Executable startup script for Windows
- `Start_Flexi_Training.desktop`: Double-clickable Linux desktop shortcut
- `dist/`: Pre-compiled production build of the React interface
- `requirements.txt`: Python package requirements freeze
- `backend/app.py`: Embedded static server + REST API
