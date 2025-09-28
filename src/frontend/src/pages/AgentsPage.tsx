import { useEffect, useState } from "react"
import { api } from "../lib/api"

interface Agent {
  id: string
  name: string
  model: string
  status: string
  created_at: string
  tools?: string[]
}

interface Tool {
  name: string
  description: string
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [models, setModels] = useState<string[]>([])
  const [tools, setTools] = useState<Tool[]>([])
  const [name, setName] = useState("")
  const [model, setModel] = useState("")
  const [selectedTools, setSelectedTools] = useState<string[]>([])

  useEffect(() => {
    refreshAgents()
    loadModels()
    loadTools()
  }, [])

  const refreshAgents = async () => {
    const data = await api<{ agents: Agent[] }>("/agents")
    setAgents(data.agents)
  }

  const loadModels = async () => {
    const data = await api<{ models: string[] }>("/models/openai")
    setModels(data.models)
    if (data.models.length > 0) setModel(data.models[0])
  }

  const loadTools = async () => {
    const data = await api<{ tools: Tool[] }>("/tools")
    setTools(data.tools)
  }

  const toggleTool = (tool: string) => {
    setSelectedTools(prev =>
      prev.includes(tool) ? prev.filter(t => t !== tool) : [...prev, tool]
    )
  }

  const createAgent = async () => {
    await api("/agents", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name, model, tools: selectedTools })
    })
    setName("")
    setSelectedTools([])
    await refreshAgents()
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Agents</h1>

      <div className="mb-6 p-4 border rounded bg-gray-50">
        <h2 className="font-semibold mb-2">Create Agent</h2>
        <input
          className="border p-2 rounded mr-2"
          placeholder="Agent name"
          value={name}
          onChange={e => setName(e.target.value)}
        />
        <select
          className="border p-2 rounded mr-2"
          value={model}
          onChange={e => setModel(e.target.value)}
        >
          {models.map(m => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        <div className="mt-3">
          <p className="font-medium mb-1">Assign Tools:</p>
          <div className="flex flex-col gap-1">
            {tools.map(tool => (
              <label key={tool.name} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedTools.includes(tool.name)}
                  onChange={() => toggleTool(tool.name)}
                />
                <span>{tool.name}</span>
                <span className="text-sm text-gray-500">
                  {tool.description}
                </span>
              </label>
            ))}
          </div>
        </div>

        <button
          onClick={createAgent}
          className="mt-3 bg-black text-white px-4 py-2 rounded"
        >
          Create
        </button>
      </div>

      <h2 className="font-semibold mb-2">Existing Agents</h2>
      <div className="grid gap-3">
        {agents.map(agent => (
          <div key={agent.id} className="p-3 border rounded bg-white shadow">
            <h3 className="font-bold">{agent.name}</h3>
            <p>Model: {agent.model}</p>
            <p>Status: {agent.status}</p>
            <p>
              Tools:{" "}
              {agent.tools && agent.tools.length > 0
                ? agent.tools.join(", ")
                : "None"}
            </p>
            <p className="text-sm text-gray-500">
              Created:{" "}
              {agent.created_at
                ? new Date(agent.created_at).toLocaleString()
                : "Unknown"}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
