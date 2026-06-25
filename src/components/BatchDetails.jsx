import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getBatchDetailStats } from '../services/api'

function BatchDetails() {
  const { batchId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBatchDetails = async () => {
      try {
        const response = await getBatchDetailStats(batchId)
        setData(response.data)
      } catch (err) {
        setError('Unable to load batch details')
      } finally {
        setLoading(false)
      }
    }

    fetchBatchDetails()
  }, [batchId])

  if (loading) {
    return <div className="p-10 text-slate-500">Loading batch details...</div>
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-slate-50 p-6">
        <div className="mx-auto max-w-4xl rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <p className="text-sm text-rose-600">{error || 'Batch details not found'}</p>
          <Link to="/batches" className="mt-3 inline-block text-sm text-blue-600">← Back to batches</Link>
        </div>
      </div>
    )
  }

  const { batch, statistics } = data

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-6xl space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Batch Details</h1>
            <p className="text-sm text-slate-500">Live information for this induction batch</p>
          </div>
          <Link to="/batches" className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white">
            ← Back to Batch Management
          </Link>
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-sm font-semibold text-slate-700">Batch Information</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs uppercase text-slate-500">Batch ID</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.id}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">Batch Name</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.batch_name}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">Category</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.category}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">Status</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.status}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">Start Date</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.start_date}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">End Date</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.end_date}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">Location</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.location}</p>
              </div>
              <div>
                <p className="text-xs uppercase text-slate-500">Coordinator Name</p>
                <p className="mt-1 text-sm font-medium text-slate-900">{batch.coordinator_name}</p>
              </div>
            </div>
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h2 className="text-sm font-semibold text-slate-700">Statistics</h2>
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span>Total Trainees</span>
                <span className="font-semibold">{statistics.total_trainees}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span>Attendance Uploaded</span>
                <span className="font-semibold">{statistics.attendance_uploaded ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span>Faculty Sessions Count</span>
                <span className="font-semibold">{statistics.faculty_sessions_count}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span>Pre-Test Uploaded</span>
                <span className="font-semibold">{statistics.pre_test_uploaded ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span>Post-Test Uploaded</span>
                <span className="font-semibold">{statistics.post_test_uploaded ? 'Yes' : 'No'}</span>
              </div>
              <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                <span>Department Allocation Uploaded</span>
                <span className="font-semibold">{statistics.department_allocated ? 'Yes' : 'No'}</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

export default BatchDetails
