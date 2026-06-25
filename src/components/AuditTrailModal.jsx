import { useEffect, useState } from 'react'
import axios from 'axios'

function AuditTrailModal({ traineeId, onClose }) {
  const [auditData, setAuditData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchAuditTrail()
  }, [traineeId])

  const fetchAuditTrail = async () => {
    try {
      const response = await axios.get(`/api/trainee-mgmt/audit-trail/${traineeId}`)
      setAuditData(response.data)
      setError('')
    } catch (err) {
      setError(err?.response?.data?.error || 'Failed to fetch audit trail')
    } finally {
      setLoading(false)
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="max-h-[90vh] w-full max-w-4xl overflow-y-auto rounded-lg bg-white shadow-lg">
        <div className="sticky top-0 border-b border-slate-200 bg-slate-50 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-900">Audit Trail</h2>
              <p className="text-sm text-slate-500">
                {auditData?.name} ({auditData?.personal_no})
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="px-6 py-4">
          {error && (
            <div className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm text-rose-700 mb-4">
              {error}
            </div>
          )}

          {auditData?.audit_trail.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-slate-500">No audit records found</p>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="mb-4 text-sm text-slate-600">
                Total Changes: <span className="font-medium">{auditData?.total_changes}</span>
              </div>
              {auditData?.audit_trail.map((record) => (
                <div key={record.id} className="rounded-lg border border-slate-200 p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="inline-block rounded-full bg-blue-100 px-2 py-1 text-xs font-medium text-blue-700">
                          {record.field}
                        </span>
                        <span className="text-xs text-slate-500">
                          {new Date(record.changed_at).toLocaleString()}
                        </span>
                      </div>
                      <div className="mt-2 grid gap-2 md:grid-cols-2">
                        <div>
                          <p className="text-xs font-medium text-slate-600">Old Value</p>
                          <div className="mt-1 rounded bg-slate-50 px-3 py-2 font-mono text-sm text-slate-700">
                            {record.old_value || <span className="text-slate-400">-</span>}
                          </div>
                        </div>
                        <div>
                          <p className="text-xs font-medium text-slate-600">New Value</p>
                          <div className="mt-1 rounded bg-emerald-50 px-3 py-2 font-mono text-sm text-emerald-700">
                            {record.new_value || <span className="text-slate-400">-</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-slate-200 bg-slate-50 px-6 py-4">
          <div className="flex justify-end">
            <button
              onClick={onClose}
              className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AuditTrailModal
