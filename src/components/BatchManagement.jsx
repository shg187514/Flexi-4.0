import { useCallback, useEffect, useMemo, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import ConfirmModal from './ConfirmModal'
import {
  createBatch,
  deleteBatch,
  getBatchDashboard,
  getBatchDetails,
  getBatches,
  updateBatch,
} from '../services/api'

const categories = [
  'Temporary',
  'Guest',
  'Learn and Earn',
  'Diploma Apprentice',
  'Job Trainee'
]

const statuses = ['Active', 'Completed']

function BatchManagement() {
  const [batches, setBatches] = useState([])
  const [dashboard, setDashboard] = useState({
    total_batches: 0,
    active_batches: 0,
    completed_batches: 0,
    category_breakdown: {},
    recent_batches: []
  })
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [selectedBatchId, setSelectedBatchId] = useState(null)
  const [selectedBatch, setSelectedBatch] = useState(null)
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const { register, handleSubmit, reset, setValue } = useForm({
    defaultValues: {
      batch_name: '',
      category: '',
      start_date: '',
      end_date: '',
      location: '',
      coordinator_name: '',
      status: 'Active'
    }
  })

  const fetchBatches = useCallback(async () => {
    try {
      const response = await getBatches({
        q: search,
        category: categoryFilter,
        status: statusFilter
      })
      setBatches(response.data)
    } catch (err) {
      setError('Unable to load batches')
    }
  }, [categoryFilter, search, statusFilter])

  const fetchDashboard = useCallback(async () => {
    try {
      const response = await getBatchDashboard()
      setDashboard(response.data)
    } catch (err) {
      setError('Unable to load batch dashboard')
    }
  }, [])

  useEffect(() => {
    fetchBatches()
  }, [fetchBatches])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  useEffect(() => {
    if (!selectedBatchId) return
    const loadSelectedBatch = async () => {
      try {
        const response = await getBatchDetails(selectedBatchId)
        setSelectedBatch(response.data)
      } catch (err) {
        setError('Unable to load batch details')
      }
    }

    loadSelectedBatch()
  }, [selectedBatchId])

  const openCreateForm = () => {
    reset({
      batch_name: '',
      category: '',
      start_date: '',
      end_date: '',
      location: '',
      coordinator_name: '',
      status: 'Active'
    })
    setSelectedBatchId(null)
    setIsFormOpen(true)
  }

  const openEditForm = (batch) => {
    setSelectedBatchId(batch.id)
    setValue('batch_name', batch.batch_name || '')
    setValue('category', batch.category || '')
    setValue('start_date', batch.start_date || '')
    setValue('end_date', batch.end_date || '')
    setValue('location', batch.location || '')
    setValue('coordinator_name', batch.coordinator_name || '')
    setValue('status', batch.status || 'Active')
    setIsFormOpen(true)
  }

  const handleSubmitBatch = async (values) => {
    if (new Date(values.end_date) < new Date(values.start_date)) {
      setError('End date cannot be earlier than start date')
      return
    }

    try {
      if (selectedBatchId) {
        await updateBatch(selectedBatchId, values)
        setMessage('Batch updated successfully')
      } else {
        await createBatch(values)
        setMessage('Batch created successfully')
      }
      setError('')
      setIsFormOpen(false)
      reset()
      fetchBatches()
      fetchDashboard()
    } catch (err) {
      setError(err?.response?.data?.error || 'Unable to save batch')
    }
  }

  const handleDeleteBatch = async () => {
    if (!confirmDelete?.id) return
    try {
      await deleteBatch(confirmDelete.id)
      setMessage('Batch deleted successfully')
      setConfirmDelete(null)
      setSelectedBatchId(null)
      setSelectedBatch(null)
      fetchBatches()
      fetchDashboard()
    } catch (err) {
      setError('Unable to delete batch')
    }
  }

  const totalCategoryEntries = useMemo(
    () => Object.entries(dashboard.category_breakdown || {}),
    [dashboard.category_breakdown]
  )

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-7xl space-y-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Batch Management</h1>
            <p className="text-sm text-slate-500">Create, edit, search, and track induction batches</p>
          </div>
          <button
            onClick={openCreateForm}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white"
          >
            + Create Batch
          </button>
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

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Total Batches</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{dashboard.total_batches}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Active</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{dashboard.active_batches}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Completed</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{dashboard.completed_batches}</p>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm text-slate-500">Categories</p>
            <p className="mt-2 text-3xl font-semibold text-slate-900">{totalCategoryEntries.length}</p>
          </div>
        </div>

        <div className="grid gap-6 xl:grid-cols-[1.5fr_0.9fr]">
          <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="flex flex-1 gap-3">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search batch name, location, or coordinator"
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                />
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">All Categories</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                >
                  <option value="">All Status</option>
                  {statuses.map((status) => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-4 overflow-hidden rounded-lg border border-slate-200">
              <div className="max-h-[500px] overflow-auto">
                <table className="min-w-full divide-y divide-slate-200 text-sm">
                  <thead className="bg-slate-50">
                    <tr>
                      <th className="px-4 py-2 text-left">Batch</th>
                      <th className="px-4 py-2 text-left">Category</th>
                      <th className="px-4 py-2 text-left">Dates</th>
                      <th className="px-4 py-2 text-left">Status</th>
                      <th className="px-4 py-2 text-left">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {batches.map((batch) => (
                      <tr key={batch.id} className="border-t">
                        <td className="px-4 py-3">
                          <Link
                            to={`/batches/${batch.id}`}
                            className="text-left font-medium text-slate-800 hover:text-blue-600"
                          >
                            {batch.batch_name}
                          </Link>
                          <p className="text-xs text-slate-500">{batch.location}</p>
                        </td>
                        <td className="px-4 py-3">{batch.category}</td>
                        <td className="px-4 py-3">{batch.start_date} → {batch.end_date}</td>
                        <td className="px-4 py-3">
                          <span className={`rounded-full px-2 py-1 text-xs ${batch.status === 'Active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}`}>
                            {batch.status}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex gap-2">
                            <button
                              onClick={() => openEditForm(batch)}
                              className="text-sm text-blue-600"
                            >
                              Edit
                            </button>
                            <button
                              onClick={() => setConfirmDelete({ id: batch.id, label: batch.batch_name })}
                              className="text-sm text-rose-600"
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <aside className="space-y-6">
            <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-sm font-semibold text-slate-700">Batch Dashboard</h2>
              <div className="mt-3 space-y-2">
                {totalCategoryEntries.map(([category, count]) => (
                  <div key={category} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
                    <span>{category}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-sm font-semibold text-slate-700">Batch Details</h2>
              {selectedBatch ? (
                <div className="mt-3 space-y-2 text-sm">
                  <p><span className="font-medium">Name:</span> {selectedBatch.batch_name}</p>
                  <p><span className="font-medium">Category:</span> {selectedBatch.category}</p>
                  <p><span className="font-medium">Coordinator:</span> {selectedBatch.coordinator_name}</p>
                  <p><span className="font-medium">Location:</span> {selectedBatch.location}</p>
                  <p><span className="font-medium">Start:</span> {selectedBatch.start_date}</p>
                  <p><span className="font-medium">End:</span> {selectedBatch.end_date}</p>
                  <p><span className="font-medium">Status:</span> {selectedBatch.status}</p>
                </div>
              ) : (
                <p className="mt-3 text-sm text-slate-500">Select a batch to view details</p>
              )}
            </section>

            <section className="rounded-xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h2 className="text-sm font-semibold text-slate-700">Recent Batches</h2>
              <div className="mt-3 space-y-2">
                {dashboard.recent_batches.map((batch) => (
                  <div key={batch.id} className="rounded-md border p-2 text-sm">
                    <p className="font-medium">{batch.batch_name}</p>
                    <p className="text-slate-500">{batch.start_date} to {batch.end_date}</p>
                  </div>
                ))}
              </div>
            </section>
          </aside>
        </div>
      </div>

      {isFormOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-xl">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                {selectedBatchId ? 'Edit Batch' : 'Create Batch'}
              </h2>
              <button onClick={() => setIsFormOpen(false)} className="text-sm text-slate-500">Close</button>
            </div>
            <form onSubmit={handleSubmit(handleSubmitBatch)} className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="md:col-span-2">
                <label className="mb-1 block text-sm font-medium">Batch Name</label>
                <input {...register('batch_name', { required: true })} className="w-full rounded-lg border px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Category</label>
                <select {...register('category', { required: true })} className="w-full rounded-lg border px-3 py-2 text-sm">
                  <option value="">Select category</option>
                  {categories.map((category) => (
                    <option key={category} value={category}>{category}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Status</label>
                <select {...register('status', { required: true })} className="w-full rounded-lg border px-3 py-2 text-sm">
                  {statuses.map((status) => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Start Date</label>
                <input type="date" {...register('start_date', { required: true })} className="w-full rounded-lg border px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">End Date</label>
                <input type="date" {...register('end_date', { required: true })} className="w-full rounded-lg border px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Location</label>
                <input {...register('location', { required: true })} className="w-full rounded-lg border px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium">Coordinator Name</label>
                <input {...register('coordinator_name', { required: true })} className="w-full rounded-lg border px-3 py-2 text-sm" />
              </div>
              <div className="md:col-span-2 flex justify-end gap-2">
                <button type="button" onClick={() => setIsFormOpen(false)} className="rounded-lg bg-slate-100 px-4 py-2 text-sm">Cancel</button>
                <button type="submit" className="rounded-lg bg-slate-900 px-4 py-2 text-sm text-white">Save Batch</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <ConfirmModal
        isOpen={!!confirmDelete}
        title="Delete batch?"
        message={`Delete ${confirmDelete?.label || 'this batch'}?`}
        onConfirm={handleDeleteBatch}
        onCancel={() => setConfirmDelete(null)}
      />
    </div>
  )
}

export default BatchManagement
