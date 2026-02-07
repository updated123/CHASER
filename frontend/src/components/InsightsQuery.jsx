import React, { useState } from 'react'
import { Search, Sparkles, Loader2, CheckCircle, XCircle } from 'lucide-react'
import axios from 'axios'

// Get API URL from environment variable, fallback to /api for local dev
const API_BASE = import.meta.env.VITE_API_URL || '/api'

const EXAMPLE_QUERIES = [
  "Which clients are underweight in equities relative to their risk profile?",
  "Show me clients with ISA allowance still available this tax year",
  "Which clients haven't had a review in over 12 months?",
  "What documents are we still waiting for from clients?",
  "Which clients have excess cash above 6 months expenditure?",
  "Show me all open action items across my client base",
  "Which business owners haven't discussed exit planning?",
  "What concerns did clients raise in meetings this month?",
]

function InsightsQuery() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleQuery = async (queryText = null) => {
    const queryToUse = queryText || query
    if (!queryToUse.trim()) return

    try {
      setLoading(true)
      setError(null)
      setResult(null)

      const response = await axios.post(
        `${API_BASE}/insights/natural-language`,
        null,
        { params: { query: queryToUse } }
      )

      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Error processing query')
      console.error('Query error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleExampleClick = (exampleQuery) => {
    setQuery(exampleQuery)
    handleQuery(exampleQuery)
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex items-center space-x-2 mb-4">
        <Sparkles className="w-6 h-6 text-primary-600" />
        <h2 className="text-xl font-bold text-gray-900">Natural Language Insights</h2>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Ask questions in plain English. The AI will understand your intent and find the relevant data.
      </p>

      {/* Query Input */}
      <div className="mb-4">
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleQuery()}
              placeholder="Ask a question... e.g., 'Which clients are underweight in equities?'"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
          <button
            onClick={() => handleQuery()}
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Search className="w-4 h-4" />
                <span>Query</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Example Queries */}
      <div className="mb-6">
        <p className="text-sm font-medium text-gray-700 mb-2">Example Queries:</p>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map((example, idx) => (
            <button
              key={idx}
              onClick={() => handleExampleClick(example)}
              className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-md text-gray-700 transition-colors"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-2">
          <XCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-red-800">Error</p>
            <p className="text-sm text-red-600">{error}</p>
          </div>
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div className="space-y-4">
          {/* Query Info */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <CheckCircle className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-800">Query Processed</p>
                <p className="text-sm text-blue-700 mt-1">"{result.query}"</p>
                <div className="mt-2 flex items-center space-x-4 text-xs text-blue-600">
                  <span>Intent: {result.intent || 'N/A'}</span>
                  <span>Confidence: {(result.confidence * 100).toFixed(0)}%</span>
                  <span>Results: {result.count || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {/* LLM Summary */}
          {result.summary && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm font-medium text-green-800 mb-2">AI Summary</p>
              <p className="text-sm text-green-700 whitespace-pre-wrap">{result.summary}</p>
            </div>
          )}

          {/* Results Table */}
          {result.results && Array.isArray(result.results) && result.results.length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    {Object.keys(result.results[0]).map((key) => (
                      <th
                        key={key}
                        className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      >
                        {key.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {result.results.slice(0, 20).map((row, idx) => (
                    <tr key={idx} className="hover:bg-gray-50">
                      {Object.values(row).map((value, colIdx) => (
                        <td key={colIdx} className="px-4 py-3 text-sm text-gray-700">
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {result.results.length > 20 && (
                <p className="mt-2 text-sm text-gray-500 text-center">
                  Showing first 20 of {result.results.length} results
                </p>
              )}
            </div>
          )}

          {/* No Results */}
          {(!result.results || result.results.length === 0) && (
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg text-center">
              <p className="text-sm text-gray-600">No results found for this query.</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default InsightsQuery

