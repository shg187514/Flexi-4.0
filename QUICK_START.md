# QUICK START GUIDE

## ⚡ Start the Application (3 Steps)

### Step 1: Start Backend (Python/Flask)
```bash
cd /home/ubuntu/Desktop/Flexi\ Training2.0/backend
python3 app.py
```
✓ Should show: `Running on http://127.0.0.1:5000`

### Step 2: Start Frontend (React/Vite) - NEW TERMINAL
```bash
cd /home/ubuntu/Desktop/Flexi\ Training2.0
npm run dev
```
✓ Should show: `Local: http://localhost:5173`

### Step 3: Open in Browser
- Go to: http://localhost:5173
- All features should work immediately

---

## 🔍 Testing Each Feature

### Dashboard
1. Open http://localhost:5173
2. Should show: Total Trainees (5), Average Attendance (%), Test scores
3. If error: Check backend is running

### Batches
1. Click "Batch Management"
2. Should show: "Interns" batch with details
3. Can create, edit, delete batches

### Upload Trainees
1. Click "Upload Trainees"
2. Should show: Upload history with 1 record
3. Can download template and upload new file

### Upload Attendance
1. Click "Attendance"
2. Should show: Attendance history with records
3. Can upload new attendance file

### Reports
1. Click "Reports"
2. Can generate: Attendance, Faculty, Pre-Test, Post-Test, Department, Complete Induction reports
3. Can export as Excel or PDF

---

## ⚠️ Troubleshooting

### "Unable to load batches"
**Solution**: Make sure backend is running in Terminal 1
```bash
cd backend && python3 app.py
```

### "Cannot connect to API"
**Solution**: 
1. Backend might not be started
2. Different port being used - check output
3. Frontend port 5173 already in use - change port:
```bash
npm run dev -- --port 5174
```

### "Page not loading"
**Solution**:
1. Check browser console (F12) for errors
2. Check Network tab - API calls should return 200
3. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### "Database error"
**Solution**: Database should exist at `backend/database/flexi_training.db`
```bash
cd backend && python3 -c "
from models import init_db
init_db()
print('Database initialized')
"
```

---

## 📊 Sample Data

The application comes with test data:

| Category | Count | Examples |
|----------|-------|----------|
| Batches | 1 | Interns |
| Trainees | 5 | Rahul Sharma, Priya Patel, Vikram Singh, etc. |
| Attendance | 5 | Day1 & Day2 status for each trainee |
| Pre-Tests | 5 | Scores (8-12 range) |
| Post-Tests | 5 | Scores (15-19 range) |
| Faculty | 5 | Session records |
| Departments | 5 | Allocations |

---

## 🚀 Production Deployment

### Build
```bash
npm run build
```
Creates `dist/` folder with optimized files

### Set Backend URL
```bash
export VITE_API_TARGET=https://your-backend.com:5000
npm run build
```

### Serve
```bash
python3 -m http.server --directory dist 8000
```
Open http://localhost:8000

---

## 📋 File Locations

- **Backend**: `/home/ubuntu/Desktop/Flexi Training2.0/backend/`
- **Frontend**: `/home/ubuntu/Desktop/Flexi Training2.0/src/`
- **Database**: `/home/ubuntu/Desktop/Flexi Training2.0/backend/database/flexi_training.db`
- **API Routes**: `/home/ubuntu/Desktop/Flexi Training2.0/backend/routes/`
- **Components**: `/home/ubuntu/Desktop/Flexi Training2.0/src/components/`
- **Config**: `/home/ubuntu/Desktop/Flexi Training2.0/vite.config.js`

---

## ✅ Verification

All systems operational:
- ✓ Backend: Python Flask running
- ✓ Database: SQLite with 8 tables
- ✓ API: All endpoints returning 200 OK
- ✓ Frontend: React/Vite compiled
- ✓ Components: All error handling in place

**Status**: Ready to use! Start backend and frontend to test.
