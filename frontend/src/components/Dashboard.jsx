import React, { useState, useEffect } from 'react'
import { format } from 'date-fns'
import StatsCards from './StatsCards'
import ChaseList from './ChaseList'
import { RefreshCw, Play } from 'lucide-react'
import axios from 'axios'
import { API_BASE } from '../config/api'

function Dashboard() {
  const [stats, setStats] = useState(null)
  const [chases, setChases] = useState([])
  const [loading, setLoading] = useState(true)
  const [runningCycle, setRunningCycle] = useState(false)
  const [filters, setFilters] = useState({
    chase_type: '',
    priority: '',
    status: ''
  })

  const fetchData = async () => {
    try {
      setLoading(true)
      
      // Wake up backend first - Render free tier can take 30-60 seconds
      const backendBase = API_BASE.replace('/api', '')
      console.log('🌙 Backend might be sleeping, attempting to wake up...')
      
      // Try health check with longer timeout for Render wake-up
      let backendAwake = false
      try {
        await axios.get(`${backendBase}/health`, { timeout: 60000 }) // 60 second timeout for wake-up
        backendAwake = true
        console.log('✅ Backend is awake')
      } catch (healthError) {
        console.warn('⚠️ Health check failed, backend is sleeping. This can take 30-60 seconds on Render free tier.')
        // Try docs endpoint as alternative wake-up method
        try {
          console.log('Trying alternative wake-up method...')
          await axios.get(`${backendBase}/docs`, { timeout: 60000 })
          backendAwake = true
          console.log('✅ Backend woke up after docs request')
          // Wait a bit for backend to fully initialize
          await new Promise(resolve => setTimeout(resolve, 3000))
        } catch (docsError) {
          console.warn('⚠️ Backend still waking up. This is normal for Render free tier - can take up to 60 seconds.')
          // Don't fail yet - try the actual API call anyway
        }
      }
      
      // Now make the actual API calls with longer timeout to account for slow wake-up
      const [statsRes, chasesRes] = await Promise.all([
        axios.get(`${API_BASE}/dashboard/stats`, { timeout: 45000 }), // 45 seconds
        axios.get(`${API_BASE}/chases/active`, { params: filters, timeout: 45000 })
      ])
      setStats(statsRes.data)
      setChases(chasesRes.data.items || [])
    } catch (error) {
      console.error('Error fetching data:', error)
      console.error('API Base URL:', API_BASE)
      console.error('VITE_API_URL:', import.meta.env.VITE_API_URL || 'NOT SET')
      console.error('Full error:', error.response || error.message)
      console.error('Error code:', error.code)
      console.error('Error details:', {
        message: error.message,
        code: error.code,
        response: error.response?.data,
        status: error.response?.status,
        headers: error.response?.headers
      })
      
      // Show user-friendly error
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        const backendUrl = API_BASE.replace('/api', '')
        alert(`Backend is taking too long to respond.\n\n⏰ Render Free Tier:\n- Services sleep after 15 min inactivity\n- Can take 30-60 seconds to wake up\n\n🔧 Solutions:\n1. Wait 30-60 seconds and refresh\n2. Open ${backendUrl}/health in new tab to wake it\n3. Consider upgrading Render plan for faster wake-up\n\n💡 Tip: First load after sleep is always slow.`)
      } else if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        const backendUrl = API_BASE.replace('/api', '')
        const viteUrl = import.meta.env.VITE_API_URL || 'NOT SET'
        alert(`Cannot connect to backend API.\n\nBackend URL: ${backendUrl}\nVITE_API_URL: ${viteUrl}\n\nPossible issues:\n1. VITE_API_URL not set in Vercel (check Settings → Environment Variables)\n2. Backend is sleeping (visit ${backendUrl}/health to wake it up)\n3. CORS not configured (set ALLOWED_ORIGINS=* in Render)\n4. Frontend needs redeploy after setting VITE_API_URL\n\nCheck browser console (F12) for detailed error.`)
      }
    } finally {
      setLoading(false)
    }
  }

  const [useLangGraph, setUseLangGraph] = useState(true)

  const runAutonomousCycle = async () => {
    try {
      setRunningCycle(true)
      const response = await axios.post(
        `${API_BASE}/agents/run-cycle`,
        null,
        { params: { use_langgraph: useLangGraph } }
      )
      console.log('Cycle result:', response.data)
      // Refresh data after cycle
      await fetchData()
      
      const actionsCount = response.data.actions_taken?.length || 0
      const summary = response.data.summary_stats || {}
      const message = `Autonomous cycle completed!\n\n` +
        `Actions taken: ${actionsCount}\n` +
        `Urgent items: ${summary.urgent_items || 0}\n` +
        `High priority: ${summary.high_priority_items || 0}\n` +
        `High stuck risk: ${summary.high_stuck_risk || 0}\n\n` +
        `Mode: ${useLangGraph ? 'LLM-Powered (LangGraph)' : 'Rule-Based'}`
      
      alert(message)
    } catch (error) {
      console.error('Error running cycle:', error)
      alert('Error running autonomous cycle: ' + (error.response?.data?.detail || error.message))
    } finally {
      setRunningCycle(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [filters])

  if (loading && !stats) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <div>
            <p className="text-lg font-medium text-gray-900">Loading dashboard...</p>
            <p className="text-sm text-gray-500 mt-2">
              {API_BASE.includes('render.com') 
                ? '⏰ Backend may be waking up (30-60 seconds on Render free tier)'
                : 'Connecting to backend...'}
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Action Bar */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={fetchData}
            className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <div className="flex items-center space-x-2">
            <label className="flex items-center space-x-2 text-sm text-gray-700">
              <input
                type="checkbox"
                checked={useLangGraph}
                onChange={(e) => setUseLangGraph(e.target.checked)}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span>Use LLM (LangGraph)</span>
            </label>
          </div>
          <button
            onClick={runAutonomousCycle}
            disabled={runningCycle}
            className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
          >
            <Play className="w-4 h-4 mr-2" />
            {runningCycle ? 'Running...' : 'Run Autonomous Cycle'}
          </button>
        </div>
        <div className="text-sm text-gray-500">
          Last updated: {format(new Date(), 'HH:mm:ss')}
        </div>
      </div>

      {/* Stats Cards */}
      {stats && <StatsCards stats={stats} />}

      {/* Filters */}
      <div className="mt-6 bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chase Type
            </label>
            <select
              value={filters.chase_type}
              onChange={(e) => setFilters({ ...filters, chase_type: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="">All Types</option>
              <option value="loa">LOA</option>
              <option value="client_document">Client Documents</option>
              <option value="post_advice">Post-Advice</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Priority
            </label>
            <select
              value={filters.priority}
              onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="">All Priorities</option>
              <option value="urgent">Urgent</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Status
            </label>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm"
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="sent">Sent</option>
              <option value="acknowledged">Acknowledged</option>
              <option value="overdue">Overdue</option>
            </select>
          </div>
        </div>
      </div>

      {/* Chase List */}
      <div className="mt-6">
        <ChaseList chases={chases} />
      </div>
    </div>
  )
}

export default Dashboard

