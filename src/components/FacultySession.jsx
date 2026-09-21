import axios from 'axios'
import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import ConfirmModal from './ConfirmModal'
import { getBatches } from '../services/api'

const API = '/api'

function FacultySession() {
  const [batches, setBatches] = useState([])
  const [sessions, setSessions] = useState([])
  const [history, setHistory] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [filePassword, setFilePassword] = useState('')
  const [isDragging, setIsDragging] = useState(false)
  const [previewRows, setPreviewRows] = useState([])
  const [showManualForm, setShowManualForm] = useState(false)
  const [form, setForm] = useState({
    batch_id: '',
    trainer_name: '',
    start_date: '',
    end_date: '',
    subject: '',
    notes: ''
  })
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(null)

  const { register, watch, reset } = useForm({
    defaultValues: { batch_id: '' }
  })

  const selectedBatchId = watch('batch_id')

  const fetchBatches = async () => {
    try {
      const response = await getBatches()
      setBatches(response.data)
    } catch (err) {
      setError('Unable to load batches')
    }
  }

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/faculty`)
      setSessions(response.data)
    } catch (err) {
      setError('Unable to load trainer sessions')
    }
  }

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/faculty/upload-history`)
      setHistory(response.data)
    } catch (err) {
      setError('Unable to load upload history')
    }
  }

  useEffect(() => {
    fetchBatches()
    fetchSessions()
    fetchHistory()
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const resetForm = () => {
    setForm({
      batch_id: '',
      trainer_name: '',
      start_date: '',
      end_date: '',
      subject: '',
      notes: ''
    })
    setEditingId(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const payload = {
        ...form,
        batch_id: selectedBatchId || form.batch_id
      }
      if (editingId) {
        await axios.put(`${API}/faculty/${editingId}`, payload)
        setMessage('Trainer session updated successfully')
      } else {
        await axios.post(`${API}/faculty`, payload)
        setMessage('Trainer session added successfully')
      }
      resetForm()
      fetchSessions()
    } catch (err) {
      setError(err?.response?.data?.error || 'Unable to save trainer session')
    }
  }

  const handleEdit = (session) => {
    setEditingId(session.id)
    setForm({
      batch_id: session.batch_id || '',
      trainer_name: session.trainer_name || session.faculty_name || '',
      start_date: session.start_date || '',
      end_date: session.end_date || '',
      subject: session.subject || session.topic || '',
      notes: session.notes || ''
    })
    setShowManualForm(true)
  }

  const handleDelete = async () => {
    if (!confirmDelete?.id) return
    try {
      await axios.delete(`${API}/faculty/${confirmDelete.id}`)
      setMessage('Trainer session deleted')
      fetchSessions()
    } catch (err) {
      setError('Unable to delete session')
    } finally {
      setConfirmDelete(null)
    }
  }

  const handleFileSelect = (file) => {
    if (!file || !file.name.match(/\.(xlsx|xls)$/i)) {
      setError('Please upload an Excel file (.xlsx or .xls)')
      return
    }
    setSelectedFile(file)
    setError('')
  }

  const handlePreview = async () => {
    if (!selectedFile || !selectedBatchId) {
      setError('Please select a batch and choose a file first')
      return
    }
    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('batch_id', selectedBatchId)
    if (filePassword) {
      formData.append('password', filePassword)
    }

    try {
      const response = await axios.post(`${API}/faculty/upload-preview`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setPreviewRows(response.data.preview || [])
      setMessage(`Preview loaded with ${response.data.total_rows} rows`)
      setError('')
    } catch (err) {
      setError(err?.response?.data?.error || 'Preview failed')
    }
  }

  const handleImport = async () => {
    if (!previewRows.length || !selectedBatchId) return
    try {
      const response = await axios.post(`${API}/faculty/import`, {
        batch_id: selectedBatchId,
        rows: previewRows,
        file_name: selectedFile?.name || 'trainer_session_import'
      })
      setMessage(response.data.message || 'Trainer sessions imported successfully')
      setPreviewRows([])
      setSelectedFile(null)
      setFilePassword('')
      reset({ batch_id: selectedBatchId })
      fetchSessions()
      fetchHistory()
    } catch (err) {
      setError(err?.response?.data?.error || 'Import failed')
    }
  }

  const totalSessions = useMemo(() => sessions.length, [sessions])

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Trainer Sessions</h1>
          <p className="text-sm text-slate-500">Manage trainer session schedules and date ranges</p>
        </div>

        {message && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">{message}</div>
        )}
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</div>
        )}

        <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-slate-700">{editingId ? 'Edit Trainer Session' : 'Manual Entry'}</h2>
              <button
                type="button"
                onClick={() => setShowManualForm((prev) => !prev)}
                className="rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white"
              >
                {showManualForm ? 'Hide' : 'Add Session'}
              </button>
            </div>
            {showManualForm && (
              <form className="space-y-3" onSubmit={handleSubmit}>
                <select className="w-full rounded-lg border px-3 py-2 text-sm" {...register('batch_id')}>
                  <option value="">Select Batch</option>
                  {batches.map((batch) => (
                    <option key={batch.id} value={batch.id}>{batch.batch_name}</option>
                  ))}
                </select>
                <input
                  name="trainer_name"
                  value={form.trainer_name}
                  onChange={handleChange}
                  placeholder="Trainer Name"
                  className="w-full rounded-lg border px-3 py-2 text-sm"
                  required
                />
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">Start Date</label>
                    <input
                      type="date"
                      name="start_date"
                      value={form.start_date}
                      onChange={handleChange}
                      className="w-full rounded-lg border px-3 py-2 text-sm"
                      required
                    />
                  </div>
                  <div>
                    <label className="mb-1 block text-xs font-medium text-slate-600">End Date</label>
                    <input
                      type="date"
                      name="end_date"
                      value={form.end_date}
                      onChange={handleChange}
                      className="w-full rounded-lg border px-3 py-2 text-sm"
                      required
                    />
                  </div>
                </div>
                <input
                  name="subject"
                  value={form.subject}
                  onChange={handleChange}
                  placeholder="Subject / Topic"
                  className="w-full rounded-lg border px-3 py-2 text-sm"
                  required
                />
                <textarea
                  name="notes"
                  value={form.notes}
                  onChange={handleChange}
                  placeholder="Notes"
                  rows="3"
                  className="w-full rounded-lg border px-3 py-2 text-sm"
                />
                <div className="flex gap-2">
                  <button className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white">
                    {editingId ? 'Update' : 'Add'}
                  </button>
                  {editingId && (
                    <button type="button" onClick={resetForm} className="rounded-lg bg-slate-200 px-4 py-2 text-sm">
                      Cancel
                    </button>
                  )}
                </div>
              </form>
            )}
          </section>

          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4 flex flex-wrap gap-3">
              <select
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register('batch_id')}
              >
                <option value="">Select Batch</option>
                {batches.map((batch) => (
                  <option key={batch.id} value={batch.id}>{batch.batch_name}</option>
                ))}
              </select>
            </div>
            <div>
              <h2 className="text-sm font-semibold text-slate-700">Upload Trainer Sessions Excel</h2>
            </div>
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFileSelect(e.dataTransfer.files?.[0]) }}
              className={`mt-3 rounded-2xl border-2 border-dashed p-8 text-center transition ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50'}`}
            >
              <input id="faculty-upload" type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => handleFileSelect(e.target.files?.[0])} />
              <label htmlFor="faculty-upload" className="cursor-pointer">
                <p className="text-sm font-medium text-slate-700">{selectedFile ? selectedFile.name : 'Drag & drop Excel file or click to browse'}</p>
                <p className="mt-1 text-xs text-slate-500">Expected columns: Start Date, End Date, Trainer Name, Subject</p>
              </label>
            </div>

            {selectedFile && (
              <div className="mt-4">
                <label className="mb-1 block text-xs font-medium text-slate-600">
                  Excel File Password (if encrypted/password-protected)
                </label>
                <input
                  type="password"
                  value={filePassword}
                  onChange={(e) => setFilePassword(e.target.value)}
                  placeholder="Enter file password if protected"
                  className="w-full max-w-sm rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
                />
              </div>
            )}

            <div className="mt-4 flex gap-2">
              <button onClick={handlePreview} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white" disabled={!selectedFile || !selectedBatchId}>Preview</button>
              <button onClick={handleImport} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white" disabled={!previewRows.length || !selectedBatchId}>Import</button>
            </div>

            {previewRows.length > 0 && (
              <div className="mt-6 overflow-hidden rounded-lg border">
                <table className="min-w-full text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-3 py-2 text-left">Start Date</th>
                      <th className="px-3 py-2 text-left">End Date</th>
                      <th className="px-3 py-2 text-left">Trainer Name</th>
                      <th className="px-3 py-2 text-left">Subject</th>
                    </tr>
                  </thead>
                  <tbody>
                    {previewRows.map((row, idx) => (
                      <tr key={idx} className="border-t">
                        <td className="px-3 py-2">{row.start_date || '-'}</td>
                        <td className="px-3 py-2">{row.end_date || '-'}</td>
                        <td className="px-3 py-2">{row.trainer_name || row.faculty_name}</td>
                        <td className="px-3 py-2">{row.subject}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-700">Trainer Sessions ({totalSessions})</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-3 py-2 text-left">Start Date</th>
                  <th className="px-3 py-2 text-left">End Date</th>
                  <th className="px-3 py-2 text-left">Trainer Name</th>
                  <th className="px-3 py-2 text-left">Subject</th>
                  <th className="px-3 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((session) => (
                  <tr key={session.id} className="border-t">
                    <td className="px-3 py-2">{session.start_date || '-'}</td>
                    <td className="px-3 py-2">{session.end_date || '-'}</td>
                    <td className="px-3 py-2">{session.trainer_name || session.faculty_name}</td>
                    <td className="px-3 py-2">{session.subject || session.topic}</td>
                    <td className="px-3 py-2">
                      <div className="flex gap-2">
                        <button onClick={() => handleEdit(session)} className="rounded bg-amber-500 px-2 py-1 text-white">Edit</button>
                        <button onClick={() => setConfirmDelete({ id: session.id, label: session.trainer_name || session.faculty_name || 'this session' })} className="rounded bg-rose-600 px-2 py-1 text-white">Delete</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h2 className="text-sm font-semibold text-slate-700">Upload History</h2>
          <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {history.map((item) => (
              <div key={item.id} className="rounded-lg border p-3 text-sm">
                <p className="font-medium">{item.file_name}</p>
                <p className="text-slate-500">{item.module_name || 'Trainer Session Upload'} · {item.status}</p>
                <p className="text-xs text-slate-500">{item.batch_id ? `Batch ${item.batch_id}` : 'Batch not set'} · {item.total_records ?? 0} records</p>
                <p className="text-xs text-slate-400">{item.uploaded_at}</p>
              </div>
            ))}
          </div>
        </section>
      </div>

      <ConfirmModal
        isOpen={!!confirmDelete}
        title="Delete session?"
        message={`Delete ${confirmDelete?.label || 'this session'}?`}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  )
}

export default FacultySession
