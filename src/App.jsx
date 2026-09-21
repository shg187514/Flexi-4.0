import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import TraineeUpload from './components/TraineeUpload'
import AttendanceUpload from './components/AttendanceUpload'
import FacultySession from './components/FacultySession'
import PostTestUpload from './components/PostTestUpload'
import PreTestUpload from './components/PreTestUpload'
import DepartmentAllocation from './components/DepartmentAllocation'
import TraineeProfile from './components/TraineeProfile'
import ReportCenter from './components/ReportCenter'
import Dashboard from './components/Dashboard'
import BatchManagement from './components/BatchManagement'
import BatchDetails from './components/BatchDetails'
import TraineeSearch from './components/TraineeSearch'
import TraineeHistory from './components/TraineeHistory'

const sidebarItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/batches', label: 'Batches' },
  { to: '/trainees', label: 'Trainee Upload' },
  { to: '/trainee-history', label: 'Trainee History' },
  { to: '/attendance', label: 'Attendance' },
  { to: '/faculty', label: 'Trainer Sessions' },
  { to: '/pretest', label: 'Pre-Test' },
  { to: '/posttest', label: 'Post-Test' },
  { to: '/department', label: 'Department Allocation' },
  { to: '/trainee-search', label: 'Trainee Search' },
  { to: '/reports', label: 'Reports' },
]

function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-slate-900 text-slate-100 lg:block">
      <div className="p-5">
        <h2 className="text-lg font-semibold">Training Hub</h2>
      </div>
      <nav className="space-y-1 px-3 pb-6">
        {sidebarItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2 text-sm transition ${
                isActive ? 'bg-slate-800 text-white' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="flex min-h-screen bg-slate-50">
        <Sidebar />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/batches" element={<BatchManagement />} />
            <Route path="/batches/:batchId" element={<BatchDetails />} />
            <Route path="/trainees" element={<TraineeUpload />} />
            <Route path="/trainee-history" element={<TraineeHistory />} />
            <Route path="/attendance" element={<AttendanceUpload />} />
            <Route path="/faculty" element={<FacultySession />} />
            <Route path="/posttest" element={<PostTestUpload />} />
            <Route path="/pretest" element={<PreTestUpload />} />
            <Route path="/department" element={<DepartmentAllocation />} />
            <Route path="/trainee-search" element={<TraineeSearch />} />
            <Route path="/profile" element={<TraineeProfile />} />
            <Route path="/reports" element={<ReportCenter />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
