import { useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import axios from 'axios'
import ConfirmModal from './ConfirmModal'

const API = '/api'

function PostTestUpload() {
  const [batches, setBatches] = useState([])
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [previewRows, setPreviewRows] = useState([])
  const [history, setHistory] = useState([])
  const [summary, setSummary] = useState({ total_records: 0, average_improvement: 0, improvement_count: 0 })
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(null)
  const { register, watch, reset } = useForm({ defaultValues: { batch_id: '' } })
  const selectedBatchId = watch('batch_id')

  const fetchBatches = async () => {
    try {
      const response = await axios.get(`${API}/batches`)
      setBatches(response.data)
    } catch (err) {
      setError('Unable to load batches')
    }
  }

  const fetchHistory = async () => {
    try {
      const response = await axios.get(`${API}/posttest/upload-history`)
      setHistory(response.data)
    } catch (err) {
      setError('Unable to load upload history')
    }
  }

  const fetchSummary = async () => {
    try {
      const response = await axios.get(`${API}/posttest/summary`, {
        params: selectedBatchId ? { batch_id: selectedBatchId } : {}
      })
      setSummary(response.data)
    } catch (err) {
      setError('Unable to load summary')
    }
  }

  useEffect(() => {
    fetchBatches()
    fetchHistory()
  }, [])

  useEffect(() => {
    fetchSummary()
  }, [selectedBatchId])

  const validateFile = (file) => {
    return !!file && /\.(xlsx|xls)$/i.test(file.name)
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
      const response = await axios.post(`${API}/posttest/upload-preview`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      setPreviewRows(response.data.preview || [])
      setMessage(`Preview loaded with ${response.data.total_rows} records`)
    } catch (err) {
      setError(err?.response?.data?.error || 'Preview failed')
    }
  }

  const handleImport = async () => {
    if (!previewRows.length || !selectedBatchId) {
      setError('Please select a batch and preview rows first')
      return
    }
    try {
      const response = await axios.post(`${API}/posttest/import`, {
        batch_id: selectedBatchId,
        rows: previewRows,
        file_name: selectedFile?.name || 'posttest_import'
      })
      setMessage(response.data.message || 'Post-test imported')
      setPreviewRows([])
      setSelectedFile(null)
      reset({ batch_id: selectedBatchId })
      fetchHistory()
      fetchSummary()
    } catch (err) {
      setError(err?.response?.data?.error || 'Import failed')
    }
  }

  const deleteHistory = async () => {
    if (!confirmDelete?.id) return
    try {
      await axios.delete(`${API}/posttest/upload-history/${confirmDelete.id}`)
      setHistory((prev) => prev.filter((item) => item.id !== confirmDelete.id))
      setMessage('History deleted')
    } catch (err) {
      setError('Could not delete history')
    } finally {
      setConfirmDelete(null)
    }
  }

  const totalPreview = useMemo(() => previewRows.length, [previewRows])

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Post-Test Module</h1>
          <p className="text-sm text-slate-500">Upload and track post-test marks</p>
        </div>

        {message && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">{message}</div>
        )}
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</div>
        )}

        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="mb-4">
              <select
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                {...register('batch_id')}
              >
                <option value="">Select Batch</option>
                {batches.map((batch) => (
                  <option key={batch.id} value={batch.id}>{batch.batch_name}</option>
                ))}
              </select>
            </div>
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => { e.preventDefault(); setIsDragging(false); handleFileSelect(e.dataTransfer.files?.[0]) }}
              className={`rounded-2xl border-2 border-dashed p-8 text-center transition ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50'}`}
            >
              <input id="posttest-upload" type="file" accept=".xlsx,.xls" className="hidden" onChange={(e) => handleFileSelect(e.target.files?.[0])} />
              <label htmlFor="posttest-upload" className="cursor-pointer">
                <p className="text-sm font-medium text-slate-700">{selectedFile ? selectedFile.name : 'Drag & drop Excel file or click to browse'}</p>
                <p className="mt-1 text-xs text-slate-500">Expected columns: Personal No, Marks</p>
              </label>
            </div>

            <div className="mt-4 flex gap-3">
              <button onClick={handlePreview} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white" disabled={!selectedFile || !selectedBatchId}>Preview Data</button>
              <button onClick={handleImport} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white" disabled={!previewRows.length || !selectedBatchId}>Import Marks</button>
            </div>

            {previewRows.length > 0 && (
              <div className="mt-6 overflow-hidden rounded-lg border border-slate-200">
                <div className="bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700">Preview ({totalPreview})</div>
                <div className="max-h-96 overflow-auto">
                  <table className="min-w-full text-sm">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-3 py-2 text-left">Personal No</th>
                        <th className="px-3 py-2 text-left">Marks</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((row, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="px-3 py-2">{row.personal_no}</td>
                          <td className="px-3 py-2">{row.marks}</td>
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
              <h2 className="text-sm font-semibold text-slate-700">Performance Summary</h2>
              <div className="mt-3 grid gap-3">
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-slate-500">Total Records</p>
                  <p className="text-2xl font-semibold">{summary.total_records}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-slate-500">Average Improvement</p>
                  <p className="text-2xl font-semibold">{summary.average_improvement}</p>
                </div>
                <div className="rounded-lg bg-slate-50 p-3">
                  <p className="text-slate-500">Improvement Records</p>
                  <p className="text-2xl font-semibold">{summary.improvement_count}</p>
                </div>
              </div>
            </section>

            <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-sm font-semibold text-slate-700">Upload History</h2>
              <div className="mt-3 space-y-3">
                {history.map((item) => (
                  <div key={item.id} className="rounded-lg border p-3 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">{item.file_name}</p>
                      <button onClick={() => setConfirmDelete({ id: item.id, label: item.file_name })} className="text-xs text-rose-600">Delete</button>
                    </div>
                    <p className="text-slate-500">{item.module_name || 'Post-Test Upload'} · {item.status}</p>
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
        onConfirm={deleteHistory}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  )
}

export default PostTestUpload
