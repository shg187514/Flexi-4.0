# Flexi Training 2.0

A full-stack training management app with a React/Vite frontend and a Flask backend.

## Features
- Batch management
- Trainee upload and search
- Attendance, pre-test, post-test, department, and faculty uploads
- Dashboard analytics
- Report generation and export

## Prerequisites
- Node.js 18+
- Python 3.10+
- Windows PowerShell or Command Prompt

## Backend setup (Windows)
1. Open PowerShell in the project root.
2. Create and activate a virtual environment:
   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install Python dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start the backend:
   ```powershell
   python app.py
   ```
   By default the backend runs on port `5000`.

## Frontend setup (Windows)
1. In a second PowerShell window, from the project root run:
   ```powershell
   npm install
   ```
2. Start the frontend:
   ```powershell
   npm run dev
   ```
3. The app will open on the Vite default URL (`http://localhost:5173`).

## Environment note for Windows
If your backend is not running on port `5000`, set the frontend API target before starting Vite:
```powershell
$env:VITE_API_TARGET = "http://localhost:8000"
npm run dev
```

## Verification
- `npm run build` verifies the frontend compiles successfully.
- `python -m compileall backend` verifies the backend syntax is valid.

## Excel upload notes
- Trainee files should include: `Name`, `Ticket No`, `Personal No`
- Attendance files should include: `Personal No`, `Day1`, `Day2`
- Department files should include: `Personal No`, `Department`
- Uploads are batch-scoped, so select a batch before importing.

