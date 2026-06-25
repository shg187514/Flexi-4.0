import { useCallback, useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import ConfirmModal from './ConfirmModal'
import {
  deleteAttendanceHistory,
  getAttendanceHistory,
  getAttendanceSummary,
  getBatches,
  importAttendance,
  uploadAttendancePreview
} from '../services/api'

function AttendanceUpload() {
  const [batches, setBatches] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [previewRows, setPreviewRows] = useState([])
  const [history, setHistory] = useState([])
  const [summary, setSummary] = useState({
    day1_present: 0,
    day1_absent: 0,
    day2_present: 0,
    day2_absent: 0
  })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(null)

  const { register, watch, reset } = useForm({
    defaultValues: { batch_id: '' }
  })

  const selectedBatchId = watch('batch_id')

  const fetchBatches = useCallback(async () => {
    try {
      const response = await getBatches()
      setBatches(response.data)
    } catch (err) {
      setError('Unable to load batches')
    }
  }, [])

  const fetchSummary = useCallback(async () => {
    try {
      const response = await getAttendanceSummary(selectedBatchId || '')
      setSummary(response.data)
    } catch (err) {
      setError('Unable to load summary')
    }
  }, [selectedBatchId])

  const fetchHistory = useCallback(async () => {
    try {
      const response = await getAttendanceHistory()
      setHistory(response.data)
    } catch (err) {
      setError('Unable to load upload history')
    }
  }, [])

  useEffect(() => {
    fetchBatches()
  }, [fetchBatches])

  useEffect(() => {
    fetchSummary()
    fetchHistory()
  }, [fetchSummary, fetchHistory])

  const validateFile = (file) => {
    if (!file) return false
    return file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls')
  }

  const handleFileSelect = (file) => {
    if (!validateFile(file)) {
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

    try {
      const response = await uploadAttendancePreview(formData)
      setPreviewRows(response.data.preview || [])
      setMessage(`Preview loaded with ${response.data.total_rows} rows`)
    } catch (err) {
      setError(err?.response?.data?.error || 'Preview failed')
    }
  }

  const handleImport = async () => {
    if (!previewRows.length || !selectedBatchId) {
      setError('No preview rows to import')
      return
    }

    try {
      const response = await importAttendance({
        batch_id: selectedBatchId,
        rows: previewRows,
        file_name: selectedFile?.name || 'attendance_import'
      })
      setMessage(response.data.message || 'Attendance imported successfully')
      setPreviewRows([])
      setSelectedFile(null)
      reset()
      fetchSummary()
      fetchHistory()
    } catch (err) {
      setError(err?.response?.data?.error || 'Import failed')
    }
  }

  const handleDeleteHistory = async () => {
    if (!confirmDelete?.id) return
    try {
      await deleteAttendanceHistory(confirmDelete.id)
      setHistory((prev) => prev.filter((item) => item.id !== confirmDelete.id))
      setMessage('Upload history removed')
    } catch (err) {
      setError('Unable to delete history')
    } finally {
      setConfirmDelete(null)
    }
  }

  const totalPreviewCount = useMemo(() => previewRows.length, [previewRows])

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Attendance Upload</h1>
          <p className="text-sm text-slate-500">Upload attendance records from Excel</p>
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

        <div className="grid gap-6 xl:grid-cols-[1.3fr_0.7fr]">
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
            <div
              onDragOver={(e) => {
                e.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault()
                setIsDragging(false)
                handleFileSelect(e.dataTransfer.files?.[0])
              }}
              className={`rounded-2xl border-2 border-dashed p-8 text-center transition ${
                isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50'
              }`}
            >
              <input
                id="attendance-upload"
                type="file"
                accept=".xlsx,.xls"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files?.[0])}
              />
              <label htmlFor="attendance-upload" className="cursor-pointer">
                <p className="text-sm font-medium text-slate-700">
                  {selectedFile ? selectedFile.name : 'Drag & drop attendance Excel here or click to browse'}
                </p>
                <p className="mt-1 text-xs text-slate-500">Expected columns: Personal No, Day1, Day2</p>
              </label>
            </div>

            <div className="mt-4 flex gap-3">
              <button
                onClick={handlePreview}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white"
                disabled={!selectedFile || !selectedBatchId}
              >
                Preview Data
              </button>
              <button
                onClick={handleImport}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white"
                disabled={!previewRows.length}
              >
                Import Attendance
              </button>
            </div>

            {previewRows.length > 0 && (
              <div className="mt-6 overflow-hidden rounded-lg border border-slate-200">
                <div className="flex items-center justify-between bg-slate-50 px-4 py-2">
                  <h2 className="text-sm font-semibold text-slate-700">Preview ({totalPreviewCount})</h2>
                </div>
                <div className="max-h-96 overflow-auto">
                  <table className="min-w-full divide-y divide-slate-200 text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-2 text-left">Personal No</th>
                        <th className="px-4 py-2 text-left">Day1</th>
                        <th className="px-4 py-2 text-left">Day2</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((row, index) => (
                        <tr key={index} className="border-t">
                          <td className="px-4 py-2">{row.personal_no}</td>
                          <td className="px-4 py-2">{row.day1}</td>
                          <td className="px-4 py-2">{row.day2}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </section>

          <aside className="space-y-6">
            <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="mb-3 text-sm font-semibold text-slate-700">Dashboard Summary</h2>
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-slate-500">Day 1 Present</p>
                  <p className="text-xl font-semibold">{summary.day1_present}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-slate-500">Day 1 Absent</p>
                  <p className="text-xl font-semibold">{summary.day1_absent}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-slate-500">Day 2 Present</p>
                  <p className="text-xl font-semibold">{summary.day2_present}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-slate-500">Day 2 Absent</p>
                  <p className="text-xl font-semibold">{summary.day2_absent}</p>
                </div>
              </div>
            </section>

            <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-sm font-semibold text-slate-700">Upload History</h2>
              <div className="mt-3 max-h-72 space-y-3 overflow-auto">
                {history.map((item) => (
                  <div key={item.id} className="rounded-md border p-3 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">{item.file_name}</p>
                      <button
                        onClick={() => setConfirmDelete({ id: item.id, label: item.file_name })}
                        className="text-xs text-rose-600"
                      >
                        Delete
                      </button>
                    </div>
                    <p className="text-slate-500">{item.module_name || 'Attendance Upload'} · {item.status}</p>
                    <p className="text-xs text-slate-500">{item.batch_id ? `Batch ${item.batch_id}` : 'Batch not set'} · {item.total_records ?? 0} records</p>
                    <p className="text-xs text-slate-400">{item.uploaded_at}</p>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </div>

      <ConfirmModal
        isOpen={!!confirmDelete}
        title="Delete upload history?"
        message={`Delete ${confirmDelete?.label || 'this upload history'}?`}
        onConfirm={handleDeleteHistory}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  )
}

export default AttendanceUpload
