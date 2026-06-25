import { useCallback, useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import ConfirmModal from './ConfirmModal'
import {
  deleteBatch,
  deleteUploadHistory,
  downloadTemplate,
  getBatches,
  getUploadHistory,
  importTrainees,
  searchTrainees,
  uploadPreview
} from '../services/api'

const REQUIRED_COLUMNS = ['Name', 'Ticket No', 'Personal No']

function TraineeUpload() {
  const [batches, setBatches] = useState([])
  const [previewRows, setPreviewRows] = useState([])
  const [uploadHistory, setUploadHistory] = useState([])
  const [search, setSearch] = useState('')
  const [searchResults, setSearchResults] = useState([])
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewMeta, setPreviewMeta] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [confirmDelete, setConfirmDelete] = useState(null)

  const { register, handleSubmit, watch, reset } = useForm({
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

  const fetchUploadHistory = useCallback(async () => {
    try {
      const response = await getUploadHistory()
      setUploadHistory(response.data)
    } catch (err) {
      setError('Unable to load upload history')
    }
  }, [])

  const handleSearch = useCallback(async (query) => {
    setSearch(query)
    try {
      const response = await searchTrainees(query)
      setSearchResults(response.data)
    } catch (err) {
      setError('Unable to search trainees')
    }
  }, [])

  useEffect(() => {
    fetchBatches()
    fetchUploadHistory()
  }, [fetchBatches, fetchUploadHistory])

  useEffect(() => {
    const timeout = setTimeout(() => handleSearch(search), 300)
    return () => clearTimeout(timeout)
  }, [search, handleSearch])

  const handleDownloadTemplate = async () => {
    try {
      const response = await downloadTemplate()
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = 'trainee_upload_template.xlsx'
      link.click()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError('Unable to download template')
    }
  }

  const validateFile = (file) => {
    if (!file) return false
    const allowed = ['.xlsx', '.xls']
    const isAllowed = allowed.some((ext) => file.name.toLowerCase().endsWith(ext))
    return isAllowed
  }

  const onFileSelect = (file) => {
    if (!validateFile(file)) {
      setError('Please upload an Excel file (.xlsx or .xls)')
      return
    }
    setSelectedFile(file)
    setError('')
  }

  const handleDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files?.[0]
    onFileSelect(file)
  }

  const handlePreview = async () => {
    if (!selectedFile || !selectedBatchId) {
      setError('Please select a batch and choose a file')
      return
    }

    const formData = new FormData()
    formData.append('file', selectedFile)
    formData.append('batch_id', selectedBatchId)

    try {
      const response = await uploadPreview(formData)
      setPreviewRows(response.data.preview || [])
      setPreviewMeta(response.data)
      setMessage(`Preview loaded for ${response.data.total_rows} records`)
    } catch (err) {
      setError(err?.response?.data?.error || 'Preview failed')
    }
  }

  const handleImport = async () => {
    if (!previewMeta || !selectedBatchId) return

    try {
      const response = await importTrainees({
        batch_id: selectedBatchId,
        rows: previewRows,
        file_name: previewMeta?.file_name || selectedFile?.name || 'trainee_import'
      })
      setMessage(response.data.message || 'Import completed')
      setPreviewRows([])
      setPreviewMeta(null)
      setSelectedFile(null)
      reset()
      fetchUploadHistory()
    } catch (err) {
      setError(err?.response?.data?.error || 'Import failed')
    }
  }

  const handleDeleteUpload = async () => {
    if (!confirmDelete?.id) return
    try {
      await deleteUploadHistory(confirmDelete.id)
      setUploadHistory((prev) => prev.filter((item) => item.id !== confirmDelete.id))
      setMessage('Upload history removed')
    } catch (err) {
      setError('Unable to delete upload history')
    } finally {
      setConfirmDelete(null)
    }
  }

  const handleDeleteBatch = async () => {
    if (!selectedBatchId) return
    try {
      await deleteBatch(selectedBatchId)
      setMessage('Batch deleted successfully')
      setSelectedFile(null)
      setPreviewRows([])
      setPreviewMeta(null)
      reset()
      fetchBatches()
    } catch (err) {
      setError('Unable to delete batch')
    } finally {
      setConfirmDelete(null)
    }
  }

  const totalPreviewCount = useMemo(() => previewRows.length, [previewRows])

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Trainee Upload</h1>
            <p className="text-sm text-slate-500">Upload trainee records using Excel</p>
          </div>
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

        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
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
              <button
                onClick={() => setConfirmDelete({ id: selectedBatchId, type: 'batch', label: 'selected batch' })}
                className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white"
                disabled={!selectedBatchId}
              >
                Delete Selected Batch
              </button>
              <button
                onClick={handleDownloadTemplate}
                className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
              >
                Download Sample Template
              </button>
            </div>

            <div
              onDragOver={(e) => {
                e.preventDefault()
                setIsDragging(true)
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`rounded-2xl border-2 border-dashed p-8 text-center transition ${
                isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-slate-50'
              }`}
            >
              <input
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => onFileSelect(e.target.files?.[0])}
                className="hidden"
                id="excel-upload"
              />
              <label htmlFor="excel-upload" className="cursor-pointer">
                <p className="text-sm font-medium text-slate-700">
                  {selectedFile ? selectedFile.name : 'Drag & drop Excel file here or click to browse'}
                </p>
                <p className="mt-1 text-xs text-slate-500">Expected columns: {REQUIRED_COLUMNS.join(', ')}</p>
              </label>
            </div>

            <div className="mt-4 flex gap-3">
              <button
                onClick={handlePreview}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                disabled={!selectedFile || !selectedBatchId}
              >
                Preview Data
              </button>
              <button
                onClick={handleImport}
                className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                disabled={!previewRows.length}
              >
                Import Data
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
                        <th className="px-4 py-2 text-left">Name</th>
                        <th className="px-4 py-2 text-left">Ticket No</th>
                        <th className="px-4 py-2 text-left">Personal No</th>
                      </tr>
                    </thead>
                    <tbody>
                      {previewRows.map((row, index) => (
                        <tr key={index} className="border-t">
                          <td className="px-4 py-2">{row.name}</td>
                          <td className="px-4 py-2">{row.ticket_no}</td>
                          <td className="px-4 py-2">{row.personal_no}</td>
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
              <h2 className="mb-3 text-sm font-semibold text-slate-700">Search Trainee</h2>
              <input
                type="text"
                value={search}
                onChange={(e) => handleSearch(e.target.value)}
                placeholder="Search by name, ticket, or personal no"
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
              <div className="mt-3 max-h-64 space-y-2 overflow-auto">
                {searchResults.map((trainee) => (
                  <div key={trainee.id} className="rounded-md bg-slate-50 p-2 text-sm">
                    <p className="font-medium">{trainee.name}</p>
                    <p className="text-slate-500">{trainee.ticket_no} · {trainee.personal_no}</p>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-700">Upload History</h2>
              </div>
              <div className="mt-3 max-h-72 space-y-3 overflow-auto">
                {uploadHistory.map((item) => (
                  <div key={item.id} className="rounded-md border p-3 text-sm">
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-medium">{item.file_name}</p>
                      <button
                        onClick={() => setConfirmDelete({ id: item.id, type: 'upload', label: item.file_name })}
                        className="text-xs text-rose-600"
                      >
                        Delete
                      </button>
                    </div>
                    <p className="text-slate-500">{item.module_name || 'Upload'} · {item.status}</p>
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
        title={confirmDelete?.type === 'batch' ? 'Delete batch?' : 'Delete upload history?'}
        message={confirmDelete?.type === 'batch'
          ? `This will delete the selected batch and related records. Continue?`
          : `Delete ${confirmDelete?.label || 'this upload history'}?`}
        onConfirm={confirmDelete?.type === 'batch' ? handleDeleteBatch : handleDeleteUpload}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  )
}

export default TraineeUpload
