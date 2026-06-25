import { useEffect, useMemo, useState } from 'react'
import ConfirmModal from './ConfirmModal'
import { deleteAttendanceRecord, deleteDepartmentRecord, deletePosttestRecord, deletePretestRecord, deleteTrainee, getTraineeProfile, searchTrainees } from '../services/api'

const tabs = ['Overview', 'Attendance', 'Pre-Test', 'Post-Test', 'Department']

function TraineeProfile() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [profile, setProfile] = useState(null)
  const [activeTab, setActiveTab] = useState('Overview')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(null)

  useEffect(() => {
    const timeout = setTimeout(async () => {
      try {
        const response = await searchTrainees(query)
        setResults(response.data)
      } catch (err) {
        setError('Unable to search trainees')
      }
    }, 300)

    return () => clearTimeout(timeout)
  }, [query])

  useEffect(() => {
    if (!selectedId) return
    loadProfile(selectedId)
  }, [selectedId])

  const improvementText = useMemo(() => {
    if (profile?.improvement === null || profile?.improvement === undefined) return 'N/A'
    return `${profile.improvement > 0 ? '+' : ''}${profile.improvement}`
  }, [profile])

  const loadProfile = async (traineeId) => {
    try {
      const response = await getTraineeProfile(traineeId)
      setProfile(response.data)
      setMessage('')
    } catch (err) {
      setError('Unable to load trainee profile')
    }
  }

  const handleDelete = async () => {
    if (!confirmDelete || !profile?.id) return
    try {
      if (confirmDelete.type === 'trainee') {
        await deleteTrainee(profile.id)
        setMessage('Trainee deleted successfully')
        setProfile(null)
        setSelectedId('')
        setQuery('')
      } else if (confirmDelete.type === 'attendance') {
        await deleteAttendanceRecord(profile.id)
        setMessage('Attendance record deleted successfully')
        await loadProfile(profile.id)
      } else if (confirmDelete.type === 'pretest') {
        await deletePretestRecord(profile.id)
        setMessage('Pre-test record deleted successfully')
        await loadProfile(profile.id)
      } else if (confirmDelete.type === 'posttest') {
        await deletePosttestRecord(profile.id)
        setMessage('Post-test record deleted successfully')
        await loadProfile(profile.id)
      } else if (confirmDelete.type === 'department') {
        await deleteDepartmentRecord(profile.id)
        setMessage('Department record deleted successfully')
        await loadProfile(profile.id)
      }
    } catch (err) {
      setError(err?.response?.data?.error || 'Unable to delete selected record')
    } finally {
      setConfirmDelete(null)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Trainee Profile</h1>
          <p className="text-sm text-slate-500">Search by name or personal number</p>
        </div>

        {message && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">
            {message}
          </div>
        )}
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">
            {error}
          </div>
        )}

        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by name or personal number"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
            />
            <div className="mt-3 max-h-[420px] space-y-2 overflow-auto">
              {results.map((item) => (
                <button
                  key={item.id}
                  onClick={() => setSelectedId(item.id)}
                  className={`w-full rounded-lg border p-3 text-left text-sm transition ${
                    selectedId === item.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                  }`}
                >
                  <p className="font-medium">{item.name}</p>
                  <p className="text-slate-500">{item.personal_no}</p>
                </button>
              ))}
            </div>
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            {!profile ? (
              <div className="flex h-full min-h-[400px] items-center justify-center text-sm text-slate-500">
                Select a trainee to view profile details
              </div>
            ) : (
              <>
                <div className="flex flex-col gap-2 border-b pb-4">
                  <h2 className="text-xl font-semibold text-slate-900">{profile.name}</h2>
                  <div className="flex flex-wrap gap-2 text-sm text-slate-500">
                    <span>Ticket: {profile.ticket_no}</span>
                    <span>•</span>
                    <span>Personal No: {profile.personal_no}</span>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Attendance</p>
                    <p className="text-lg font-semibold">{profile.attendance?.status || 'N/A'}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Pre-Test</p>
                    <p className="text-lg font-semibold">{profile.pre_test?.score ?? 'N/A'}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Post-Test</p>
                    <p className="text-lg font-semibold">{profile.post_test?.score ?? 'N/A'}</p>
                  </div>
                  <div className="rounded-lg bg-slate-50 p-3">
                    <p className="text-xs text-slate-500">Improvement</p>
                    <p className="text-lg font-semibold">{improvementText}</p>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  <button onClick={() => setConfirmDelete({ type: 'trainee' })} className="rounded-lg bg-rose-600 px-3 py-2 text-sm font-medium text-white">Delete Trainee</button>
                  <button onClick={() => setConfirmDelete({ type: 'attendance' })} className="rounded-lg bg-slate-200 px-3 py-2 text-sm">Delete Attendance</button>
                  <button onClick={() => setConfirmDelete({ type: 'pretest' })} className="rounded-lg bg-slate-200 px-3 py-2 text-sm">Delete Pre-Test</button>
                  <button onClick={() => setConfirmDelete({ type: 'posttest' })} className="rounded-lg bg-slate-200 px-3 py-2 text-sm">Delete Post-Test</button>
                  <button onClick={() => setConfirmDelete({ type: 'department' })} className="rounded-lg bg-slate-200 px-3 py-2 text-sm">Delete Department</button>
                </div>

                <div className="mt-5 flex flex-wrap gap-2 border-b pb-3">
                  {tabs.map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`rounded-full px-3 py-1.5 text-sm ${
                        activeTab === tab ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {tab}
                    </button>
                  ))}
                </div>

                <div className="mt-5 space-y-4">
                  {activeTab === 'Overview' && (
                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="rounded-lg border p-4">
                        <p className="text-xs uppercase text-slate-500">Personal Details</p>
                        <div className="mt-2 space-y-1 text-sm">
                          <p><span className="font-medium">Name:</span> {profile.name}</p>
                          <p><span className="font-medium">Ticket No:</span> {profile.ticket_no}</p>
                          <p><span className="font-medium">Personal No:</span> {profile.personal_no}</p>
                        </div>
                      </div>
                      <div className="rounded-lg border p-4">
                        <p className="text-xs uppercase text-slate-500">Batch Details</p>
                        <div className="mt-2 space-y-1 text-sm">
                          <p><span className="font-medium">Batch:</span> {profile.batch?.batch_name || 'N/A'}</p>
                          <p><span className="font-medium">Category:</span> {profile.batch?.category || 'N/A'}</p>
                          <p><span className="font-medium">Status:</span> {profile.batch?.status || 'N/A'}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {activeTab === 'Attendance' && (
                    <div className="rounded-lg border p-4">
                      <p className="text-xs uppercase text-slate-500">Attendance</p>
                      <div className="mt-2 space-y-1 text-sm">
                        <p><span className="font-medium">Date:</span> {profile.attendance?.attendance_date || 'N/A'}</p>
                        <p><span className="font-medium">Status:</span> {profile.attendance?.status || 'N/A'}</p>
                        <p><span className="font-medium">Remarks:</span> {profile.attendance?.remarks || 'N/A'}</p>
                      </div>
                    </div>
                  )}

                  {activeTab === 'Pre-Test' && (
                    <div className="rounded-lg border p-4">
                      <p className="text-xs uppercase text-slate-500">Pre-Test Marks</p>
                      <div className="mt-2 space-y-1 text-sm">
                        <p><span className="font-medium">Score:</span> {profile.pre_test?.score ?? 'N/A'}</p>
                        <p><span className="font-medium">Date:</span> {profile.pre_test?.test_date || 'N/A'}</p>
                        <p><span className="font-medium">Remarks:</span> {profile.pre_test?.remarks || 'N/A'}</p>
                      </div>
                    </div>
                  )}

                  {activeTab === 'Post-Test' && (
                    <div className="rounded-lg border p-4">
                      <p className="text-xs uppercase text-slate-500">Post-Test Marks</p>
                      <div className="mt-2 space-y-1 text-sm">
                        <p><span className="font-medium">Score:</span> {profile.post_test?.score ?? 'N/A'}</p>
                        <p><span className="font-medium">Date:</span> {profile.post_test?.test_date || 'N/A'}</p>
                        <p><span className="font-medium">Remarks:</span> {profile.post_test?.remarks || 'N/A'}</p>
                      </div>
                    </div>
                  )}

                  {activeTab === 'Department' && (
                    <div className="rounded-lg border p-4">
                      <p className="text-xs uppercase text-slate-500">Department Allocation</p>
                      <div className="mt-2 space-y-1 text-sm">
                        <p><span className="font-medium">Department:</span> {profile.department?.department || 'N/A'}</p>
                        <p><span className="font-medium">Allocated Date:</span> {profile.department?.allocated_date || 'N/A'}</p>
                        <p><span className="font-medium">Remarks:</span> {profile.department?.remarks || 'N/A'}</p>
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </section>
        </div>
      </div>

      <ConfirmModal
        isOpen={!!confirmDelete}
        title={confirmDelete?.type === 'trainee' ? 'Delete trainee?' : 'Delete related record?'}
        message={confirmDelete?.type === 'trainee'
          ? 'This will permanently delete the selected trainee record. Continue?'
          : 'This will remove the selected related record for this trainee. Continue?'}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  )
}

export default TraineeProfile
