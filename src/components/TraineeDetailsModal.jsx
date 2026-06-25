import { useEffect, useState } from 'react'
import axios from 'axios'

function TraineeDetailsModal({ traineeId, onClose }) {
  const [details, setDetails] = useState(null)
  const [formData, setFormData] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    fetchDetails()
  }, [traineeId])

  const fetchDetails = async () => {
    try {
      const response = await axios.get(`/api/trainee-mgmt/details/${traineeId}`)
      setDetails(response.data)
      setFormData(response.data)
      setError('')
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to fetch details')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleSave = async () => {
    setSaving(true)
    setError('')
    setSuccess('')

    try {
      const payload = {}
      
      // Only send changed fields
      if (formData.name !== details.name) payload.name = formData.name
      if (formData.ticket_no !== details.ticket_no) payload.ticket_no = formData.ticket_no
      if (formData.category !== details.category) payload.category = formData.category
      if (formData.day1_status !== details.day1_status) payload.day1_status = formData.day1_status
      if (formData.day2_status !== details.day2_status) payload.day2_status = formData.day2_status
      if (formData.pre_test_marks !== details.pre_test_marks) payload.pre_test_marks = formData.pre_test_marks
      if (formData.post_test_marks !== details.post_test_marks) payload.post_test_marks = formData.post_test_marks
      if (formData.department !== details.department) payload.department = formData.department

      if (Object.keys(payload).length === 0) {
        setError('No changes made')
        setSaving(false)
        return
      }

      await axios.put(`/api/trainee-mgmt/update/${traineeId}`, payload)
      setSuccess('Trainee updated successfully')
      setTimeout(() => {
        onClose()
      }, 1500)
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to update trainee')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
        <div className="rounded-lg bg-white p-6">
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!details) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-lg">
        <div className="sticky top-0 border-b border-slate-200 bg-slate-50 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Edit Trainee Details</h2>
              <p className="text-sm text-slate-500">{details.personal_no} - {details.batch_name}</p>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="space-y-6 px-6 py-4">
          {error && (
            <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</div>
          )}
          {success && (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">{success}</div>
          )}

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-700">Personal Information</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Name</label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Ticket Number</label>
                <input
                  type="text"
                  value={formData.ticket_no || ''}
                  onChange={(e) => handleChange('ticket_no', e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-700">Batch Information</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Category</label>
                <input
                  type="text"
                  value={formData.category || ''}
                  onChange={(e) => handleChange('category', e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Department</label>
                <input
                  type="text"
                  value={formData.department || ''}
                  onChange={(e) => handleChange('department', e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-700">Attendance</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Day 1 Status</label>
                <select
                  value={formData.day1_status || ''}
                  onChange={(e) => handleChange('day1_status', e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">Select</option>
                  <option value="Present">Present</option>
                  <option value="Absent">Absent</option>
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Day 2 Status</label>
                <select
                  value={formData.day2_status || ''}
                  onChange={(e) => handleChange('day2_status', e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">Select</option>
                  <option value="Present">Present</option>
                  <option value="Absent">Absent</option>
                </select>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-700">Test Scores</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm text-slate-600">Pre-Test Marks</label>
                <input
                  type="number"
                  value={formData.pre_test_marks || ''}
                  onChange={(e) => handleChange('pre_test_marks', e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm text-slate-600">Post-Test Marks</label>
                <input
                  type="number"
                  value={formData.post_test_marks || ''}
                  onChange={(e) => handleChange('post_test_marks', e.target.value ? parseInt(e.target.value) : null)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            </div>
          </div>
        </div>

        <div className="border-t border-slate-200 bg-slate-50 px-6 py-4">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:bg-blue-400"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default TraineeDetailsModal
