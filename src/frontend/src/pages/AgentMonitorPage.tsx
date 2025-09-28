import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { api } from "../lib/api"

interface Agent {
  id: string
  name: string
  model: string
  status: string
  created_at: string
  last_seen: string
}

interface Trace {
  timestamp: string
  type: string
  content: string
}

export default function AgentMonitorPage() {
  const { agentId } = useParams<{ agentId: string }>()
  const [agent, setAgent] = useState<Agent | null>(null)
  const [traces, setTraces] = useState<Trace[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!agentId) return

    const fetchData = () => {
      api<{ agent: Agent }>(`/agents/${agentId}`)
        .then(data => setAgent(data.agent))
        .catch(() => setAgent(null))

      api<{ traces: Trace[] }>(`/agents/${agentId}/traces`)
        .then(data => setTraces(data.traces))
        .catch(() => setTraces([]))

      setLoading(false)
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [agentId])

  if (loading) return <p className="p-6">Loading agent info...</p>
  if (!agent) return <p className="p-6">Agent not found.</p>

  return (
    <div className="p-6 space-y-6">
      <div>
        <Link to="/monitor" className="text-blue-600 hover:underline text-sm">
          ← Back to monitor list
        </Link>
      </div>

      <div className="border rounded p-4 bg-gray-50">
        <h1 className="text-xl font-bold mb-2">{agent.name}</h1>
        <p className="text-sm text-gray-700">
          Model: {agent.model} • Status:{" "}
          <span
            className={
              agent.status === "idle"
                ? "text-green-600"
                : agent.status === "running"
                ? "text-blue-600"
                : "text-red-600"
            }
          >
            {agent.status}
          </span>
        </p>
        <p className="text-xs text-gray-500">
          Created: {new Date(agent.created_at).toLocaleString()} • Last seen:{" "}
          {agent.last_seen ? new Date(agent.last_seen).toLocaleString() : "–"}
        </p>
      </div>

      <div>
        <h2 className="font-medium mb-2">Trace</h2>
        {traces.length === 0 ? (
          <p className="text-sm text-gray-500">No traces yet</p>
        ) : (
          <div className="space-y-2">
            {traces.map((t, i) => (
              <div
                key={i}
                className="border rounded p-2 bg-white text-sm shadow-sm"
              >
                <span className="text-xs text-gray-400 mr-2">
                  {new Date(t.timestamp).toLocaleTimeString()}
                </span>
                <span className="font-medium">{t.type}:</span>{" "}
                <span>{t.content}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
