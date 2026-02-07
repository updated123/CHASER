import React, { useState } from 'react'
import { format } from 'date-fns'
import { FileText, Mail, Phone, MessageSquare, Clock, AlertCircle, Brain, ChevronDown, ChevronUp } from 'lucide-react'

function ChaseList({ chases }) {
  const [expandedItems, setExpandedItems] = useState(new Set())

  const toggleExpand = (id) => {
    const newExpanded = new Set(expandedItems)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedItems(newExpanded)
  }

  const getPriorityColor = (priority) => {
    const colors = {
      urgent: 'bg-red-100 text-red-800 border-red-200',
      high: 'bg-orange-100 text-orange-800 border-orange-200',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      low: 'bg-gray-100 text-gray-800 border-gray-200'
    }
    return colors[priority] || colors.medium
  }

  const getChaseTypeIcon = (type) => {
    const icons = {
      loa: FileText,
      client_document: FileText,
      post_advice: Mail
    }
    return icons[type] || FileText
  }

  const getStuckScoreColor = (score) => {
    if (score >= 0.7) return 'text-red-600 font-bold'
    if (score >= 0.5) return 'text-orange-600 font-semibold'
    if (score >= 0.3) return 'text-yellow-600'
    return 'text-gray-600'
  }

  if (chases.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        No active chases found
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">
          Active Chases ({chases.length})
        </h2>
      </div>
      <div className="divide-y divide-gray-200">
        {chases.map((chase) => {
          const Icon = getChaseTypeIcon(chase.chase_type)
          return (
            <div
              key={chase.id}
              className="px-6 py-4 hover:bg-gray-50 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <Icon className="w-5 h-5 text-gray-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <p className="text-sm font-medium text-gray-900">
                          {chase.client_name}
                        </p>
                        <span className="text-xs text-gray-500">
                          ({chase.chase_type.replace('_', ' ')})
                        </span>
                        {chase.days_overdue > 0 && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-red-100 text-red-800">
                            <AlertCircle className="w-3 h-3 mr-1" />
                            {chase.days_overdue}d overdue
                          </span>
                        )}
                      </div>
                      <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                        {chase.details?.provider_name && (
                          <span>Provider: {chase.details.provider_name}</span>
                        )}
                        {chase.details?.document_type && (
                          <span>Doc: {chase.details.document_type.replace('_', ' ')}</span>
                        )}
                        {chase.details?.item_type && (
                          <span>Item: {chase.details.item_type.replace('_', ' ')}</span>
                        )}
                        <span>Chases: {chase.chase_count}</span>
                        {chase.last_chased_at && (
                          <span>
                            Last: {format(new Date(chase.last_chased_at), 'MMM d')}
                          </span>
                        )}
                      </div>
                      {/* LLM Reasoning Indicator */}
                      {(chase.llm_reasoning || chase.llm_priority_reasoning) && (
                        <button
                          onClick={() => toggleExpand(chase.id)}
                          className="mt-2 flex items-center space-x-1 text-xs text-primary-600 hover:text-primary-700"
                        >
                          <Brain className="w-3 h-3" />
                          <span>AI Reasoning</span>
                          {expandedItems.has(chase.id) ? (
                            <ChevronUp className="w-3 h-3" />
                          ) : (
                            <ChevronDown className="w-3 h-3" />
                          )}
                        </button>
                      )}
                      {/* Expanded LLM Reasoning */}
                      {expandedItems.has(chase.id) && (chase.llm_reasoning || chase.llm_priority_reasoning) && (
                        <div className="mt-2 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                          <p className="text-xs font-medium text-blue-800 mb-1">AI Analysis:</p>
                          {chase.llm_priority_reasoning && (
                            <p className="text-xs text-blue-700 mb-1">
                              <strong>Priority:</strong> {chase.llm_priority_reasoning}
                            </p>
                          )}
                          {chase.llm_reasoning && (
                            <p className="text-xs text-blue-700">
                              <strong>Decision:</strong> {chase.llm_reasoning}
                            </p>
                          )}
                          {chase.llm_chase_reasoning && (
                            <p className="text-xs text-blue-700 mt-1">
                              <strong>Chase Timing:</strong> {chase.llm_chase_reasoning}
                            </p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                <div className="ml-4 flex items-center space-x-3">
                  <div className="text-right">
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getPriorityColor(
                        chase.priority
                      )}`}
                    >
                      {chase.priority}
                    </span>
                    <div className="mt-1">
                      <span
                        className={`text-xs ${getStuckScoreColor(chase.stuck_score)}`}
                      >
                        Stuck: {(chase.stuck_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    {chase.llm_urgency_score !== undefined && (
                      <div className="mt-1">
                        <span className="text-xs text-gray-500">
                          Urgency: {(chase.llm_urgency_score * 100).toFixed(0)}%
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default ChaseList

