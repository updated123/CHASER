import React, { useState } from 'react'
import Dashboard from './components/Dashboard'
import InsightsQuery from './components/InsightsQuery'
import { Zap, LayoutDashboard, Sparkles } from 'lucide-react'

function App() {
  const [activeTab, setActiveTab] = useState('dashboard')

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Agentic Chaser</h1>
              <p className="text-sm text-gray-500">LLM-Powered Autonomous Document & LOA Management</p>
            </div>
            <div className="flex items-center space-x-2">
              <Zap className="w-5 h-5 text-primary-600" />
              <span className="text-sm font-medium text-gray-700">AI-Powered with Groq</span>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'dashboard'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <LayoutDashboard className="w-5 h-5" />
              <span>Dashboard</span>
            </button>
            <button
              onClick={() => setActiveTab('insights')}
              className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'insights'
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <Sparkles className="w-5 h-5" />
              <span>Natural Language Insights</span>
            </button>
          </nav>
        </div>
      </div>

      <main>
        {activeTab === 'dashboard' && <Dashboard />}
        {activeTab === 'insights' && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <InsightsQuery />
          </div>
        )}
      </main>
    </div>
  )
}

export default App

