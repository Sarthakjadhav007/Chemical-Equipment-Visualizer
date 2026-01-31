import React, { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title
} from 'chart.js'
import { Pie } from 'react-chartjs-2'
import { Upload, History, FileText, BarChart3, Download, FlaskConical, Search, LogOut, Key } from 'lucide-react'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000/api"

function App() {
  const [data, setData] = useState(null)
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [isAuthenticated, setIsAuthenticated] = useState(!!localStorage.getItem('auth'))
  const [loginData, setLoginData] = useState({ username: '', password: '' })

  const authHeader = useMemo(() => {
    const auth = localStorage.getItem('auth')
    return auth ? { Authorization: `Basic ${auth}` } : {}
  }, [isAuthenticated])

  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    if (isAuthenticated) {
      fetchHistory()
      fetchSummary()
    }
  }, [isAuthenticated])

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/history/`, { headers: authHeader })
      setHistory(res.data)
    } catch (err) {
      if (err.response?.status === 401) handleLogout()
    }
  }

  const fetchSummary = async (id = null) => {
    setLoading(true)
    try {
      const url = id ? `${API_BASE}/summary/${id}/` : `${API_BASE}/summary/`
      const res = await axios.get(url, { headers: authHeader })
      setData(res.data)
      setError(null)
    } catch (err) {
      if (err.response?.status === 401) handleLogout()
      else {
        setError("No data available. Please upload a CSV.")
        setData(null)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    try {
      await axios.post(`${API_BASE}/upload/`, formData, { headers: { ...authHeader, 'Content-Type': 'multipart/form-data' } })
      fetchSummary()
      fetchHistory()
    } catch (err) {
      alert("Upload failed: " + (err.response?.data?.error || err.message))
    } finally {
      setUploading(false)
    }
  }

  const handleLogin = (e) => {
    e.preventDefault()
    const token = btoa(`${loginData.username}:${loginData.password}`)
    localStorage.setItem('auth', token)
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    localStorage.removeItem('auth')
    setIsAuthenticated(false)
    setData(null)
  }

  const downloadPDF = () => {
    if (!data) return
    // Simple way to handle protected PDF download
    axios.get(`${API_BASE}/pdf/${data.id}/`, {
      headers: authHeader,
      responseType: 'blob'
    }).then(res => {
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `report_${data.id}.pdf`)
      document.body.appendChild(link)
      link.click()
    })
  }

  const filteredItems = useMemo(() => {
    if (!data?.data) return []
    return data.data.filter(item =>
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.type.toLowerCase().includes(searchTerm.toLowerCase())
    )
  }, [data, searchTerm])

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="glass-card w-full max-w-md space-y-8">
          <div className="text-center">
            <FlaskConical className="mx-auto text-indigo-500" size={48} />
            <h2 className="mt-6 text-3xl font-extrabold text-white">Sign In</h2>
            <p className="mt-2 text-sm text-slate-400">Access ChemVisualizer Dashboard</p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleLogin}>
            <div className="rounded-md shadow-sm space-y-4">
              <div>
                <input
                  type="text"
                  required
                  className="appearance-none relative block w-full px-3 py-3 border border-white/10 bg-white/5 rounded-lg placeholder-slate-500 text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Username (e.g. admin)"
                  value={loginData.username}
                  onChange={e => setLoginData({ ...loginData, username: e.target.value })}
                />
              </div>
              <div>
                <input
                  type="password"
                  required
                  className="appearance-none relative block w-full px-3 py-3 border border-white/10 bg-white/5 rounded-lg placeholder-slate-500 text-white focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                  placeholder="Password (e.g. admin123)"
                  value={loginData.password}
                  onChange={e => setLoginData({ ...loginData, password: e.target.value })}
                />
              </div>
            </div>
            <button type="submit" className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white btn-primary">
              <span className="absolute left-0 inset-y-0 flex items-center pl-3">
                <Key className="h-5 w-5 text-indigo-300" aria-hidden="true" />
              </span>
              Sign in
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="p-6 border-b border-white/10 flex justify-between items-center glass-card rounded-none sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <FlaskConical className="text-indigo-500" size={32} />
          <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
            ChemVisualizer
          </h1>
        </div>
        <div className="flex gap-4 items-center">
          <label className="btn-primary flex items-center gap-2 cursor-pointer">
            <Upload size={18} />
            Upload CSV
            <input type="file" onChange={handleFileUpload} className="hidden" accept=".csv" />
          </label>
          <button onClick={downloadPDF} disabled={!data} className="btn-primary bg-indigo-900/50 flex items-center gap-2 disabled:opacity-50">
            <Download size={18} />
            Report
          </button>
          <button onClick={handleLogout} className="p-2 text-slate-400 hover:text-white transition-colors">
            <LogOut size={20} />
          </button>
        </div>
      </nav>

      {/* Upload Processing Overlay */}
      {uploading && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-card flex flex-col items-center gap-4 p-10 animate-pulse">
            <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
            <h2 className="text-xl font-bold text-white">Calculating the Result...</h2>
            <p className="text-slate-400">Analyzing chemical equipment parameters</p>
          </div>
        </div>
      )}

      <main className="grid-dashboard">
        {/* Statistics Cards */}
        {data && (
          <>
            <div className="glass-card summary-stat">
              <h3>Total Equipment</h3>
              <p>{data.total_count}</p>
            </div>
            <div className="glass-card summary-stat">
              <h3>Avg. Flowrate</h3>
              <p>{data.averages.flowrate.toFixed(2)}</p>
            </div>
            <div className="glass-card summary-stat">
              <h3>Avg. Pressure</h3>
              <p>{data.averages.pressure.toFixed(2)}</p>
            </div>
          </>
        )}

        {/* Charts */}
        {data ? (
          <>
            <div className="glass-card col-span-1 md:col-span-2">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <BarChart3 className="text-indigo-400" /> Equipment Type Distribution
              </h2>
              <div className="h-[300px] flex justify-center">
                <Pie
                  data={{
                    labels: Object.keys(data.type_distribution),
                    datasets: [{
                      data: Object.values(data.type_distribution),
                      backgroundColor: [
                        '#6366f1', '#06b6d4', '#ec4899', '#f59e0b', '#10b981', '#ef4444'
                      ],
                      borderWidth: 0
                    }]
                  }}
                  options={{ maintainAspectRatio: false, plugins: { legend: { labels: { color: '#94a3b8' } } } }}
                />
              </div>
            </div>

            <div className="glass-card col-span-1 md:col-span-1">
              <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <History className="text-indigo-400" /> Recent Uploads
              </h2>
              <div className="space-y-3 overflow-y-auto max-h-[300px] pr-2">
                {history.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => fetchSummary(item.id)}
                    className="p-3 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 cursor-pointer transition-colors"
                  >
                    <div className="font-medium">{item.file_name}</div>
                    <div className="text-xs text-slate-400">{new Date(item.uploaded_at).toLocaleString()}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Data Table */}
            <div className="glass-card col-span-full">
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <h2 className="text-xl font-semibold flex items-center gap-2">
                  <FileText className="text-indigo-400" /> Equipment Parameters Table
                </h2>
                <div className="relative w-full md:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                  <input
                    type="text"
                    placeholder="Search equipment..."
                    className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:border-indigo-500 transition-colors"
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left">
                  <thead>
                    <tr className="border-b border-white/10 text-slate-400 text-sm">
                      <th className="pb-3 px-4">Name</th>
                      <th className="pb-3 px-4">Type</th>
                      <th className="pb-3 px-4">Flowrate</th>
                      <th className="pb-3 px-4">Pressure</th>
                      <th className="pb-3 px-4">Temp</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {filteredItems.map((item, i) => (
                      <tr key={i} className="hover:bg-white/5 transition-colors">
                        <td className="py-3 px-4 font-medium">{item.name}</td>
                        <td className="py-3 px-4 text-slate-400">{item.type}</td>
                        <td className="py-3 px-4 text-indigo-300">{item.flowrate}</td>
                        <td className="py-3 px-4 text-emerald-300">{item.pressure}</td>
                        <td className="py-3 px-4 text-orange-300">{item.temperature}</td>
                      </tr>
                    ))}
                    {filteredItems.length === 0 && (
                      <tr>
                        <td colSpan="5" className="py-10 text-center text-slate-500">No matching equipment found.</td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        ) : (
          <div className="col-span-full py-20 text-center glass-card">
            {loading ? (
              <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-slate-400">Processing data...</p>
              </div>
            ) : error || "Upload a CSV to get started"}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
