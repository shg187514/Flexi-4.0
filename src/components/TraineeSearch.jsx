import { useEffect, useMemo, useState } from 'react'
import { getTraineeProfile, searchTrainees } from '../services/api'

function AttendanceBadge({ status }) {
  const bgColor = status && status.toLowerCase() === 'present' ? 'bg-emerald-100 text-emerald-700' : 'bg-rose-100 text-rose-700'
  return <span className={`inline-block rounded-full px-2 py-1 text-xs font-medium ${bgColor}`}>{status || '-'}</span>
}

function TraineeSearch() {
  const [nameQuery, setNameQuery] = useState('')
  const [personalNoQuery, setPersonalNoQuery] = useState('')
  const [results, setResults] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [profile, setProfile] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    const timeout = setTimeout(async () => {
      try {
        const response = await searchTrainees({
          name: nameQuery,
          personal_no: personalNoQuery,
        })
        setResults(response.data || [])
        setError('')
      } catch (err) {
        setError('Unable to search trainees')
      }
    }, 300)

    return () => clearTimeout(timeout)
  }, [nameQuery, personalNoQuery])

  useEffect(() => {
    if (!selectedId) {
      setProfile(null)
      return
    }

    const loadProfile = async () => {
      try {
        const response = await getTraineeProfile(selectedId)
        setProfile(response.data)
      } catch (err) {
        setError('Unable to load trainee details')
      }
    }

    loadProfile()
  }, [selectedId])

  const hasFilters = useMemo(
    () => Boolean(nameQuery.trim() || personalNoQuery.trim()),
    [nameQuery, personalNoQuery]
  )

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Trainee Search</h1>
          <p className="text-sm text-slate-500">Search trainees by name or personal number</p>
        </div>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">
            {error}
          </div>
        )}

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Name</label>
              <input
                type="text"
                value={nameQuery}
                onChange={(e) => setNameQuery(e.target.value)}
                placeholder="Search by name"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Personal Number</label>
              <input
                type="text"
                value={personalNoQuery}
                onChange={(e) => setPersonalNoQuery(e.target.value)}
                placeholder="Search by personal number"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
        </section>

        <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-700">Results</h2>
              <span className="text-sm text-slate-500">{results.length} found</span>
            </div>
            <div className="mt-4 overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead>
                  <tr className="border-b bg-slate-50 text-slate-600">
                    <th className="px-3 py-2 font-medium">Name</th>
                    <th className="px-3 py-2 font-medium">Personal No</th>
                    <th className="px-3 py-2 font-medium">Ticket No</th>
                    <th className="px-3 py-2 font-medium">Batch</th>
                    <th className="px-3 py-2 font-medium">Category</th>
                    <th className="px-3 py-2 font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {results.map((item) => (
                    <tr key={item.id} className="border-b last:border-0 hover:bg-slate-50">
                      <td className="px-3 py-3">{item.name}</td>
                      <td className="px-3 py-3">{item.personal_no}</td>
                      <td className="px-3 py-3">{item.ticket_no}</td>
                      <td className="px-3 py-3">{item.batch_name || 'N/A'}</td>
                      <td className="px-3 py-3">{item.category || 'N/A'}</td>
                      <td className="px-3 py-3">
                        <button
                          onClick={() => setSelectedId(item.id)}
                          className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                            selectedId === item.id
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                          }`}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!hasFilters && (
              <p className="mt-4 text-sm text-slate-500">Use the filters above to search the trainee list.</p>
            )}
            {hasFilters && results.length === 0 && (
              <p className="mt-4 text-sm text-slate-500">No trainees matched the current search.</p>
            )}
          </section>

          {profile && (
            <section className="max-h-[70vh] space-y-4 overflow-y-auto">
              {/* Personal Information */}
              <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Personal Information</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Name:</span>
                    <span className="font-medium text-slate-900">{profile.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Personal No:</span>
                    <span className="font-medium text-slate-900">{profile.personal_no}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Ticket No:</span>
                    <span className="font-medium text-slate-900">{profile.ticket_no}</span>
                  </div>
                  {profile.batch && (
                    <div className="flex justify-between">
                      <span className="text-slate-600">Category:</span>
                      <span className="font-medium text-slate-900">{profile.batch.category}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Induction Details */}
              {profile.batch && (
                <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Induction Details</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Batch:</span>
                      <span className="font-medium text-slate-900">{profile.batch.batch_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Category:</span>
                      <span className="font-medium text-slate-900">{profile.batch.category}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Duration:</span>
                      <span className="font-medium text-slate-900">{profile.batch.start_date} to {profile.batch.end_date}</span>
                    </div>
                    {profile.batch.location && (
                      <div className="flex justify-between">
                        <span className="text-slate-600">Location:</span>
                        <span className="font-medium text-slate-900">{profile.batch.location}</span>
                      </div>
                    )}
                    {profile.batch.coordinator_name && (
                      <div className="flex justify-between">
                        <span className="text-slate-600">Coordinator:</span>
                        <span className="font-medium text-slate-900">{profile.batch.coordinator_name}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Attendance Details */}
              <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Attendance Details</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Day 1:</span>
                    <AttendanceBadge status={profile.attendance.day1_status} />
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Day 2:</span>
                    <AttendanceBadge status={profile.attendance.day2_status} />
                  </div>
                  <div className="border-t border-slate-200 pt-2">
                    <div className="mb-2 flex justify-between">
                      <span className="text-slate-600">Present Days:</span>
                      <span className="font-medium text-emerald-600">{profile.attendance.present_days}</span>
                    </div>
                    <div className="mb-2 flex justify-between">
                      <span className="text-slate-600">Absent Days:</span>
                      <span className="font-medium text-rose-600">{profile.attendance.absent_days}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-600">Attendance %:</span>
                      <span className="inline-block rounded-full bg-blue-100 px-2 py-1 font-medium text-blue-700">
                        {profile.attendance.attendance_percent}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Test Performance */}
              <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Test Performance</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Pre-Test:</span>
                    <span className="font-medium text-slate-900">{profile.pre_test.score ?? '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Post-Test:</span>
                    <span className="font-medium text-slate-900">{profile.post_test.score ?? '-'}</span>
                  </div>
                  <div className="border-t border-slate-200 pt-2">
                    <div className="flex justify-between">
                      <span className="text-slate-600">Improvement:</span>
                      {profile.improvement !== null ? (
                        <span className={`font-medium ${profile.improvement >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                          {profile.improvement >= 0 ? '+' : ''}{profile.improvement}
                        </span>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Department */}
              {profile.department.department && (
                <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Department Allocation</h3>
                  <div className="text-sm">
                    <span className="inline-block rounded-full bg-purple-100 px-3 py-1 font-medium text-purple-700">
                      {profile.department.department}
                    </span>
                  </div>
                </div>
              )}

              {/* Faculty Sessions */}
              {profile.faculty_sessions.length > 0 && (
                <div className="rounded-xl bg-white p-4 shadow-sm ring-1 ring-slate-200">
                  <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">Faculty Sessions ({profile.faculty_sessions.length})</h3>
                  <div className="space-y-2">
                    {profile.faculty_sessions.map((session) => (
                      <div key={session.id} className="border-b border-slate-200 pb-2 last:border-0">
                        <p className="text-xs font-medium text-slate-900">{session.faculty_name}</p>
                        <p className="text-xs text-slate-600">{session.topic}</p>
                        <p className="text-xs text-slate-500">
                          {session.session_date} {session.start_time && `${session.start_time}`} {session.end_time && `- ${session.end_time}`}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )}

          {!profile && (
            <section className="flex h-64 items-center justify-center rounded-xl bg-white shadow-sm ring-1 ring-slate-200">
              <p className="text-sm text-slate-500">Select a trainee to view profile</p>
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

export default TraineeSearch
