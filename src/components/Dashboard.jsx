import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import {
  Bar,
  Doughnut,
  Line,
  PolarArea,
  Radar,
  Scatter,
} from 'react-chartjs-2'
import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  RadialLinearScale,
  Tooltip,
} from 'chart.js'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  RadialLinearScale,
  Filler,
  Tooltip,
  Legend,
)

const cardClass = 'rounded-2xl border border-slate-200 bg-white p-5 shadow-sm'
const sections = ['Overview', 'Attendance', 'Performance', 'Departments']

function Dashboard() {
  const [data, setData] = useState(null)
  const [attendanceMetrics, setAttendanceMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeSection, setActiveSection] = useState('Overview')

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [overviewRes, metricsRes] = await Promise.all([
          axios.get('/api/dashboard/overview'),
          axios.get('/api/dashboard/attendance-metrics'),
        ])
        setData(overviewRes.data)
        setAttendanceMetrics(metricsRes.data)
      } catch (err) {
        console.error(err)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  const attendanceChart = useMemo(() => {
    const labels = Object.keys(data?.attendance_breakdown || {})
    const values = labels.map((key) => data.attendance_breakdown[key])
    return {
      labels,
      datasets: [{
        label: 'Attendance',
        data: values,
        backgroundColor: ['#0f766e', '#ef4444', '#3b82f6'],
        borderColor: '#fff',
        borderWidth: 1,
      }]
    }
  }, [data])

  const categoryChart = useMemo(() => {
    const labels = Object.keys(data?.category_breakdown || {})
    const values = labels.map((key) => data.category_breakdown[key])
    return {
      labels,
      datasets: [{
        data: values,
        backgroundColor: ['#2563eb', '#7c3aed', '#06b6d4', '#f59e0b', '#ec4899'],
      }]
    }
  }, [data])

  const departmentChart = useMemo(() => {
    const labels = Object.keys(data?.department_breakdown || {})
    const values = labels.map((key) => data.department_breakdown[key])
    return {
      labels,
      datasets: [{
        data: values,
        backgroundColor: ['#10b981', '#14b8a6', '#0ea5e9', '#6366f1', '#f97316'],
      }]
    }
  }, [data])

  const comparisonChart = useMemo(() => {
    const labels = data?.pre_scores && data?.post_scores
      ? data.pre_scores.map((_, i) => `T${i + 1}`)
      : []
    return {
      labels,
      datasets: [
        {
          label: 'Pre-Test',
          data: data?.pre_scores || [],
          borderColor: '#0ea5e9',
          backgroundColor: 'rgba(14,165,233,0.15)',
          fill: true,
          tension: 0.3,
        },
        {
          label: 'Post-Test',
          data: data?.post_scores || [],
          borderColor: '#22c55e',
          backgroundColor: 'rgba(34,197,94,0.12)',
          fill: true,
          tension: 0.3,
        },
      ]
    }
  }, [data])

  if (loading || !data || !attendanceMetrics) {
    return <div className="p-10 text-slate-500">Loading dashboard...</div>
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Training Dashboard</h1>
            <p className="text-sm text-slate-500">Corporate insights across batches, performance, and allocation</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              to="/batches"
              className="rounded-full bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Manage Batches
            </Link>
            <Link
              to="/trainees"
              className="rounded-full bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700"
            >
              Upload Trainees
            </Link>
            <Link
              to="/attendance"
              className="rounded-full bg-amber-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-700"
            >
              Upload Attendance
            </Link>
            <Link
              to="/faculty"
              className="rounded-full bg-violet-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-violet-700"
            >
              Upload Faculty
            </Link>
            <Link
              to="/pretest"
              className="rounded-full bg-pink-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-pink-700"
            >
              Upload Pre-Test
            </Link>
            <Link
              to="/posttest"
              className="rounded-full bg-orange-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-orange-700"
            >
              Upload Post-Test
            </Link>
            <Link
              to="/department"
              className="rounded-full bg-cyan-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-cyan-700"
            >
              Upload Department
            </Link>
            <Link
              to="/reports"
              className="rounded-full bg-indigo-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Report Center
            </Link>
            <Link
              to="/trainee-search"
              className="rounded-full bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700"
            >
              Search Trainees
            </Link>
            {sections.map((section) => (
              <button
                key={section}
                type="button"
                onClick={() => setActiveSection(section)}
                className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                  activeSection === section
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {section}
              </button>
            ))}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
          <div className={cardClass}>
            <p className="text-sm text-slate-500">Total Batches</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{data.total_batches}</p>
          </div>
          <div className={cardClass}>
            <p className="text-sm text-slate-500">Total Trainees</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{data.total_trainees}</p>
          </div>
          <div className={cardClass}>
            <p className="text-sm text-slate-500">Average Attendance</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{data.average_attendance}%</p>
          </div>
          <div className={cardClass}>
            <p className="text-sm text-slate-500">Average Pre-Test</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{data.average_pre_test}</p>
          </div>
          <div className={cardClass}>
            <p className="text-sm text-slate-500">Average Post-Test</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{data.average_post_test}</p>
          </div>
          <div className={cardClass}>
            <p className="text-sm text-slate-500">Average Improvement</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{data.average_improvement}</p>
          </div>
        </div>

        {activeSection === 'Overview' && (
          <>
            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-700">Attendance Chart</h3>
                <div className="mt-4 h-72">
                  <Bar data={attendanceChart} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-700">Category Distribution</h3>
                <div className="mt-4 h-72">
                  <Doughnut data={categoryChart} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
            </div>

            <div className="grid gap-6 xl:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-700">Department Distribution</h3>
                <div className="mt-4 h-72">
                  <PolarArea data={departmentChart} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-slate-700">Pre vs Post Test Comparison</h3>
                <div className="mt-4 h-72">
                  <Line data={comparisonChart} options={{ responsive: true, maintainAspectRatio: false }} />
                </div>
              </div>
            </div>
          </>
        )}

        {activeSection === 'Attendance' && (
          <div className="grid gap-6">
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Day 1 Present</p>
                <p className="mt-2 text-3xl font-semibold text-green-600">{attendanceMetrics?.day1_present || 0}</p>
              </div>
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Day 1 Absent</p>
                <p className="mt-2 text-3xl font-semibold text-red-600">{attendanceMetrics?.day1_absent || 0}</p>
              </div>
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Day 2 Present</p>
                <p className="mt-2 text-3xl font-semibold text-green-600">{attendanceMetrics?.day2_present || 0}</p>
              </div>
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Day 2 Absent</p>
                <p className="mt-2 text-3xl font-semibold text-red-600">{attendanceMetrics?.day2_absent || 0}</p>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Total Present</p>
                <p className="mt-2 text-3xl font-semibold text-green-600">{attendanceMetrics?.total_present || 0}</p>
              </div>
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Total Absent</p>
                <p className="mt-2 text-3xl font-semibold text-red-600">{attendanceMetrics?.total_absent || 0}</p>
              </div>
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Total Opportunities</p>
                <p className="mt-2 text-3xl font-semibold text-slate-900">{attendanceMetrics?.total_opportunities || 0}</p>
              </div>
              <div className={cardClass}>
                <p className="text-sm text-slate-500">Attendance Percentage</p>
                <p className="mt-2 text-3xl font-semibold text-blue-600">{attendanceMetrics?.attendance_percentage || 0}%</p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700">Attendance Chart</h3>
              <div className="mt-4 h-72">
                <Bar data={attendanceChart} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        )}

        {activeSection === 'Performance' && (
          <div className="grid gap-6 xl:grid-cols-1">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700">Pre vs Post Test Comparison</h3>
              <div className="mt-4 h-72">
                <Line data={comparisonChart} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        )}

        {activeSection === 'Departments' && (
          <div className="grid gap-6 xl:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700">Department Distribution</h3>
              <div className="mt-4 h-72">
                <PolarArea data={departmentChart} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-slate-700">Category Distribution</h3>
              <div className="mt-4 h-72">
                <Doughnut data={categoryChart} options={{ responsive: true, maintainAspectRatio: false }} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard
