import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

export const getBatches = (params = {}) => api.get('/batches', { params })
export const createBatch = (payload) => api.post('/batches', payload)
export const updateBatch = (id, payload) => api.put(`/batches/${id}`, payload)
export const deleteBatch = (id) => api.delete(`/batches/${id}`)
export const getBatchDetails = (id) => api.get(`/batches/${id}`)
export const getBatchDetailStats = (id) => api.get(`/batches/${id}/details`)
export const getBatchDashboard = () => api.get('/batches/dashboard')
export const searchTrainees = (params = {}) => {
  const normalizedParams = typeof params === 'string'
    ? { q: params }
    : params

  return api.get('/trainees/search', { params: normalizedParams })
}
export const getTraineeProfile = (traineeId) => api.get(`/trainees/${traineeId}/profile`)
export const deleteTrainee = (traineeId) => api.delete(`/trainees/${traineeId}`)
export const downloadTemplate = () => api.get('/trainees/download-template', { responseType: 'blob' })
export const uploadPreview = (formData) => api.post('/trainees/upload-preview', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const importTrainees = (payload) => api.post('/trainees/import', payload)
export const getUploadHistory = () => api.get('/trainees/upload-history')
export const deleteUploadHistory = (id) => api.delete(`/trainees/upload-history/${id}`)

export const uploadAttendancePreview = (formData) => api.post('/attendance/upload-preview', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const importAttendance = (payload) => api.post('/attendance/import', payload)
export const getAttendanceHistory = () => api.get('/attendance/upload-history')
export const deleteAttendanceHistory = (id) => api.delete(`/attendance/upload-history/${id}`)
export const deleteAttendanceRecord = (traineeId) => api.delete(`/attendance/record/${traineeId}`)
export const getAttendanceSummary = (batchId = '') => api.get('/attendance/summary', {
  params: batchId ? { batch_id: batchId } : {}
})

export const uploadPretestPreview = (formData) => api.post('/pretest/upload-preview', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const importPretest = (payload) => api.post('/pretest/import', payload)
export const getPretestHistory = () => api.get('/pretest/upload-history')
export const deletePretestHistory = (id) => api.delete(`/pretest/upload-history/${id}`)
export const deletePretestRecord = (traineeId) => api.delete(`/pretest/record/${traineeId}`)

export const uploadDepartmentPreview = (formData) => api.post('/department/upload-preview', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const importDepartment = (payload) => api.post('/department/import', payload)
export const getDepartmentHistory = () => api.get('/department/upload-history')
export const deleteDepartmentHistory = (id) => api.delete(`/department/upload-history/${id}`)
export const deleteDepartmentRecord = (traineeId) => api.delete(`/department/record/${traineeId}`)
export const getDepartmentSummary = (batchId = '') => api.get('/department/summary', {
  params: batchId ? { batch_id: batchId } : {}
})

export const uploadPosttestPreview = (formData) => api.post('/posttest/upload-preview', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
})
export const importPosttest = (payload) => api.post('/posttest/import', payload)
export const getPosttestHistory = () => api.get('/posttest/upload-history')
export const deletePosttestHistory = (id) => api.delete(`/posttest/upload-history/${id}`)
export const deletePosttestRecord = (traineeId) => api.delete(`/posttest/record/${traineeId}`)
export const getPosttestSummary = () => api.get('/posttest/summary')
