import { useEffect, useMemo, useState } from 'react'
import axios from 'axios'

const reportTypes = [
  { value: 'attendance', label: 'Attendance Report' },
  { value: 'trainer', label: 'Trainer Report' },
  { value: 'pre_test', label: 'Pre-Test Report' },
  { value: 'post_test', label: 'Post-Test Report' },
  { value: 'department', label: 'Department Report' },
  { value: 'complete_induction', label: 'Complete Induction Report' }
]

function ReportCenter() {
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [batchId, setBatchId] = useState('')
  const [batchSearch, setBatchSearch] = useState('')
  const [showBatchDropdown, setShowBatchDropdown] = useState(false)
  const [category, setCategory] = useState('')
  const [trainerName, setTrainerName] = useState('')
  const [subject, setSubject] = useState('')
  const [reportType, setReportType] = useState('attendance')
  const [batches, setBatches] = useState([])
  const [previewRows, setPreviewRows] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchBatches = async () => {
      try {
        const response = await axios.get('/api/batches')
        setBatches(response.data)
      } catch (err) {
        setError('Unable to load batches')
      }
    }

    fetchBatches()
  }, [])

  useEffect(() => {
    setPreviewRows([])
    setMessage('')
    setError('')
  }, [reportType])

  useEffect(() => {
    const handleClickOutside = (e) => {
      if (showBatchDropdown && !e.target.closest('.batch-search-container')) {
        setShowBatchDropdown(false)
      }
    }
    document.addEventListener('click', handleClickOutside)
    return () => document.removeEventListener('click', handleClickOutside)
  }, [showBatchDropdown])

  const filteredBatches = useMemo(() => {
    if (!batchSearch.trim()) return batches
    return batches.filter((batch) =>
      batch.batch_name.toLowerCase().includes(batchSearch.toLowerCase())
    )
  }, [batchSearch, batches])

  const selectedBatchName = useMemo(() => {
    const batch = batches.find((b) => b.id === parseInt(batchId))
    return batch ? batch.batch_name : ''
  }, [batchId, batches])

  const handleSelectBatch = (batch) => {
    setBatchId(batch.id)
    setBatchSearch(batch.batch_name)
    setShowBatchDropdown(false)
  }

  const handleClearBatch = () => {
    setBatchId('')
    setBatchSearch('')
  }

  const handleGenerateReport = async () => {
    setError('')
    setMessage('')
    try {
      const isTrainer = reportType === 'trainer'
      const response = await axios.post('/api/reports/preview', {
        report_type: reportType,
        from_date: fromDate || null,
        to_date: isTrainer ? (fromDate || null) : (toDate || null),
        batch_id: isTrainer ? null : (batchId || null),
        category: isTrainer ? null : (category || null),
        trainer_name: null,
        subject: null
      })
      setPreviewRows(response.data.rows || [])
      setMessage(`Preview generated with ${response.data.rows?.length || 0} rows`)
    } catch (err) {
      setError(err?.response?.data?.error || 'Unable to generate report')
    }
  }

  const handleExport = async (type) => {
    if (!previewRows.length) {
      setError('Generate a report first')
      return
    }

    try {
      const isTrainer = reportType === 'trainer'
      const response = await axios.post(
        `/api/reports/export/${type}`,
        {
          report_type: reportType,
          from_date: fromDate || null,
          to_date: isTrainer ? (fromDate || null) : (toDate || null),
          batch_id: isTrainer ? null : (batchId || null),
          category: isTrainer ? null : (category || null),
          trainer_name: null,
          subject: null
        },
        { responseType: 'blob' }
      )

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.download = `${reportType}_${type}.` + (type === 'excel' ? 'xlsx' : 'pdf')
      link.click()
      window.URL.revokeObjectURL(url)
      setMessage(`${type === 'excel' ? 'Excel' : 'PDF'} download started`)
    } catch (err) {
      setError(err?.response?.data?.error || `Unable to download ${type}`)
    }
  }

  const handleClearFilters = () => {
    setFromDate('')
    setToDate('')
    setBatchId('')
    setBatchSearch('')
    setCategory('')
    setTrainerName('')
    setSubject('')
    setPreviewRows([])
    setMessage('')
    setError('')
  }

  const columns = useMemo(() => previewRows[0] ? Object.keys(previewRows[0]) : [], [previewRows])

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Report Center</h1>
          <p className="text-sm text-slate-500">Filter, preview, and export reports</p>
        </div>

        {message && (
          <div className="rounded-md border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm text-emerald-700">{message}</div>
        )}
        {error && (
          <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700">{error}</div>
        )}

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
            {reportType === 'trainer' ? (
              <div>
                <label className="mb-1 block text-sm text-slate-600">Date</label>
                <input
                  type="date"
                  value={fromDate}
                  onChange={(e) => {
                    setFromDate(e.target.value)
                    setToDate(e.target.value)
                  }}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
              </div>
            ) : (
              <>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">From Date</label>
                  <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">To Date</label>
                  <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                </div>

                <div className="relative batch-search-container">
                  <label className="mb-1 block text-sm text-slate-600">Batch</label>
                  <div className="relative">
                    <input
                      type="text"
                      value={batchSearch}
                      onChange={(e) => {
                        setBatchSearch(e.target.value)
                        setShowBatchDropdown(true)
                      }}
                      onFocus={() => setShowBatchDropdown(true)}
                      placeholder="Search batches..."
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                    />
                    {batchId && (
                      <button
                        onClick={handleClearBatch}
                        className="absolute right-2 top-2 text-slate-400 hover:text-slate-600"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                  {showBatchDropdown && (
                    <div className="absolute top-full z-10 mt-1 w-full rounded-lg border border-slate-300 bg-white shadow-lg">
                      {filteredBatches.length > 0 ? (
                        <ul className="max-h-48 overflow-y-auto">
                          {filteredBatches.map((batch) => (
                            <li key={batch.id}>
                              <button
                                onClick={() => handleSelectBatch(batch)}
                                className={`w-full border-b px-3 py-2 text-left text-sm transition ${
                                  batchId === batch.id
                                    ? 'bg-blue-50 text-blue-700 font-medium'
                                    : 'text-slate-700 hover:bg-slate-50'
                                }`}
                              >
                                {batch.batch_name}
                              </button>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <div className="px-3 py-2 text-sm text-slate-500">No batches found</div>
                      )}
                    </div>
                  )}
                </div>
                <div>
                  <label className="mb-1 block text-sm text-slate-600">Category</label>
                  <input type="text" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="e.g. Tech" className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
                </div>
              </>
            )}

            <div>
              <label className="mb-1 block text-sm text-slate-600">Report Type</label>
              <select value={reportType} onChange={(e) => setReportType(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm">
                {reportTypes.map((type) => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap gap-3">
            <button onClick={handleGenerateReport} className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white">Generate Report</button>
            <button onClick={handleClearFilters} className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">Clear Filters</button>
            <button onClick={() => handleExport('excel')} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white">Download Excel</button>
            <button onClick={() => handleExport('pdf')} className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white">Download PDF</button>
          </div>
        </section>

        <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
          <h2 className="text-sm font-semibold text-slate-700">Preview</h2>
          <div className="mt-3 max-h-[520px] overflow-auto rounded-lg border border-slate-200">
            {previewRows.length > 0 ? (
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    {columns.map((col) => (
                      <th key={col} className="whitespace-nowrap px-3 py-2 text-left">{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {previewRows.map((row, index) => (
                    <tr key={index} className="border-t">
                      {columns.map((col) => (
                        <td key={col} className="px-3 py-2">{row[col] ?? ''}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="p-6 text-center text-sm text-slate-500">No preview data yet.</div>
            )}
          </div>
        </section>
      </div>
    </div>
  )
}

export default ReportCenter
