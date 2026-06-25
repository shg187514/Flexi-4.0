import { useEffect, useState } from 'react'
import axios from 'axios'
import TraineeDetailsModal from './TraineeDetailsModal'
import AuditTrailModal from './AuditTrailModal'

function TraineeHistory() {
  const [searchType, setSearchType] = useState('personal_no')
  const [searchQuery, setSearchQuery] = useState('')
  const [trainees, setTrainees] = useState([])
  const [selectedTrainee, setSelectedTrainee] = useState(null)
  const [history, setHistory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [showDetailsModal, setShowDetailsModal] = useState(false)
  const [showAuditModal, setShowAuditModal] = useState(false)
  const [selectedTraineeId, setSelectedTraineeId] = useState(null)

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setError('Please enter a search value')
      return
    }

    setLoading(true)
    setError('')
    try {
      const params = {}
      params[searchType] = searchQuery
      const response = await axios.get('/api/trainee-mgmt/search', { params })
      setTrainees(response.data.trainees || [])
      setHistory(null)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to search trainees')
      setTrainees([])
    } finally {
      setLoading(false)
    }
  }

  const handleSelectTrainee = async (trainee) => {
    setSelectedTrainee(trainee)
    setLoading(true)
    try {
      const response = await axios.get(`/api/trainee-mgmt/history/${trainee.personal_no}`)
      setHistory(response.data)
      setError('')
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to fetch trainee history')
      setHistory(null)
    } finally {
      setLoading(false)
    }
  }

  const handleOpenDetails = (traineeId) => {
    setSelectedTraineeId(traineeId)
    setShowDetailsModal(true)
  }

  const handleOpenAudit = (traineeId) => {
    setSelectedTraineeId(traineeId)
    setShowAuditModal(true)
  }

  const handleDetailsClose = () => {
    setShowDetailsModal(false)
    setSelectedTraineeId(null)
    // Refresh history
    if (selectedTrainee) {
      handleSelectTrainee(selectedTrainee)
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Trainee History</h1>
          <p className="text-sm text-slate-500">Search and manage trainee records across all batches</p>
        </div>

        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</div>
        )}

        {/* Search Section */}
        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="space-y-4">
            <div className="grid gap-4 md:grid-cols-4">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Search By</label>
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="personal_no">Personal Number</option>
                  <option value="name">Name</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Search Value</label>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder={searchType === 'personal_no' ? 'e.g., EMP001' : 'e.g., John Doe'}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleSearch}
                  disabled={loading}
                  className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-blue-400"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
              </div>
            </div>
          </div>
        </section>

        {/* Search Results */}
        {trainees.length > 0 && !history && (
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="mb-4 text-sm font-semibold text-slate-700">Search Results ({trainees.length})</h2>
            <div className="grid gap-3">
              {trainees.map((trainee) => (
                <button
                  key={trainee.id}
                  onClick={() => handleSelectTrainee(trainee)}
                  className="rounded-lg border border-slate-200 bg-slate-50 p-4 text-left hover:bg-blue-50"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{trainee.name}</p>
                      <p className="text-xs text-slate-500">Personal No: {trainee.personal_no} | Ticket: {trainee.ticket_no}</p>
                    </div>
                    <div className="text-right text-xs text-slate-600">
                      <p>{trainee.batch_name}</p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Trainee History */}
        {history && (
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="mb-6 border-b border-slate-200 pb-4">
              <h2 className="text-lg font-semibold text-slate-900">{history.trainee_info.name}</h2>
              <p className="text-sm text-slate-500">
                Personal No: {history.trainee_info.personal_no} | Ticket No: {history.trainee_info.ticket_no}
              </p>
              <p className="mt-2 text-sm text-slate-600">
                Total Batches Attended: <span className="font-medium">{history.total_batches}</span>
              </p>
            </div>

            {history.batches.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="whitespace-nowrap px-3 py-2 text-left font-medium text-slate-600">Batch Name</th>
                      <th className="whitespace-nowrap px-3 py-2 text-left font-medium text-slate-600">Category</th>
                      <th className="whitespace-nowrap px-3 py-2 text-left font-medium text-slate-600">Dates</th>
                      <th className="whitespace-nowrap px-3 py-2 text-center font-medium text-slate-600">Attendance %</th>
                      <th className="whitespace-nowrap px-3 py-2 text-center font-medium text-slate-600">Pre-Test</th>
                      <th className="whitespace-nowrap px-3 py-2 text-center font-medium text-slate-600">Post-Test</th>
                      <th className="whitespace-nowrap px-3 py-2 text-center font-medium text-slate-600">Improvement</th>
                      <th className="whitespace-nowrap px-3 py-2 text-left font-medium text-slate-600">Department</th>
                      <th className="whitespace-nowrap px-3 py-2 text-center font-medium text-slate-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.batches.map((batch, idx) => (
                      <tr key={idx} className="border-t border-slate-200">
                        <td className="px-3 py-2 font-medium text-slate-900">{batch.batch_name}</td>
                        <td className="px-3 py-2 text-slate-600">{batch.category}</td>
                        <td className="whitespace-nowrap px-3 py-2 text-xs text-slate-600">
                          {batch.start_date} to {batch.end_date}
                        </td>
                        <td className="px-3 py-2 text-center font-medium text-slate-900">{batch.attendance_percent}%</td>
                        <td className="px-3 py-2 text-center text-slate-600">{batch.pre_test_marks ?? '-'}</td>
                        <td className="px-3 py-2 text-center text-slate-600">{batch.post_test_marks ?? '-'}</td>
                        <td className="px-3 py-2 text-center font-medium text-slate-900">{batch.improvement ?? '-'}</td>
                        <td className="px-3 py-2 text-slate-600">{batch.department ?? '-'}</td>
                        <td className="px-3 py-2 text-center">
                          <div className="flex justify-center gap-2">
                            <button
                              onClick={() => handleOpenDetails(batch.trainee_id)}
                              className="rounded px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => handleOpenAudit(batch.trainee_id)}
                              className="rounded px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100"
                            >
                              Audit
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-center text-slate-500">No batch records found</p>
            )}
          </section>
        )}

        {/* Modals */}
        {showDetailsModal && (
          <TraineeDetailsModal
            traineeId={selectedTraineeId}
            onClose={handleDetailsClose}
          />
        )}
        {showAuditModal && (
          <AuditTrailModal
            traineeId={selectedTraineeId}
            onClose={() => setShowAuditModal(false)}
          />
        )}
      </div>
    </div>
  )
}

export default TraineeHistory
