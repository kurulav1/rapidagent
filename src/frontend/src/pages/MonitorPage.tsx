import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "../lib/api"

interface Agent {
  id: string
  name: string
  model: string
  status: string
  created_at: string
}

export default function MonitorPage() {
  const [agents, setAgents] = useState<Agent[]>([])

  useEffect(() => {
    const fetchAgents = () => {
      api<{ agents: Agent[] }>("/agents")
        .then(data => setAgents(data.agents))
        .catch(err => console.error("Failed to load agents", err))
    }
    fetchAgents()
    const interval = setInterval(fetchAgents, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Agent Monitor</h1>
      {agents.length === 0 && (
        <p className="text-gray-500">No agents detected</p>
      )}
      <div className="space-y-3">
        {agents.map(agent => (
          <Link
            key={agent.id}
            to={`/monitor/${agent.id}`}
            className="block border rounded p-4 hover:bg-gray-50"
          >
            <h2 className="font-medium">{agent.name}</h2>
            <p className="text-sm text-gray-600">
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
            <p className="text-xs text-gray-400">
              Created: {new Date(agent.created_at).toLocaleString()}
            </p>
          </Link>
        ))}
      </div>
    </div>
  )
}
