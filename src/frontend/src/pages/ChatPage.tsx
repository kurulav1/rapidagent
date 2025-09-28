import { useEffect, useState } from "react"
import { api } from "../lib/api"

interface Agent {
  id: string
  name: string
  model: string
  status: string
  system_prompt?: string
}

interface AgentDetails {
  agent: Agent
  tools: string[]
  messages: { role: string; content: string; timestamp?: string }[]
}

export default function ChatPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>("")
  const [agentDetails, setAgentDetails] = useState<AgentDetails | null>(null)
  const [message, setMessage] = useState("")
  const [chat, setChat] = useState<{ role: string; content: string }[]>([])

  useEffect(() => {
    api<{ agents: Agent[] }>("/agents")
      .then(data => {
        setAgents(data.agents)
        if (data.agents.length > 0) setSelectedAgent(data.agents[0].id)
      })
      .catch(err => console.error("Failed to load agents", err))
  }, [])

  useEffect(() => {
    if (selectedAgent) {
      api<AgentDetails>(`/agents/${selectedAgent}`)
        .then(data => {
          setAgentDetails(data)
          setChat(data.messages || [])
        })
        .catch(err => console.error("Failed to load agent details", err))
    }
  }, [selectedAgent])

  const sendMessage = async () => {
    if (!selectedAgent || !message.trim()) return
    const newChat = [...chat, { role: "user", content: message }]
    setChat(newChat)
    setMessage("")
    try {
      const res = await api<{ messages: { role: string; content: string }[] }>(
        `/agents/${selectedAgent}/chat`,
        {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: JSON.stringify({ messages: [{ role: "user", content: message }] }),
        }
      )
      setChat(res.messages)
    } catch (e) {
      console.error(e)
    }
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Chat</h1>

      <div className="mb-4">
        <label className="block font-medium mb-1">Select Agent</label>
        <select
          value={selectedAgent}
          onChange={e => setSelectedAgent(e.target.value)}
          className="border rounded p-2 w-full"
        >
          {agents.map(agent => (
            <option key={agent.id} value={agent.id}>
              {agent.name} ({agent.model}) – {agent.status}
            </option>
          ))}
        </select>
      </div>

      {agentDetails && (
        <div className="mb-4 p-3 border rounded bg-gray-100">
          <p><b>Model:</b> {agentDetails.agent.model}</p>
          <p><b>Status:</b> {agentDetails.agent.status}</p>
          <p><b>Tools:</b> {agentDetails.tools.join(", ") || "None"}</p>
          {agentDetails.agent.system_prompt && (
            <p><b>System Prompt:</b> {agentDetails.agent.system_prompt}</p>
          )}
        </div>
      )}

      <div className="border rounded p-4 h-64 overflow-y-auto bg-gray-50">
        {chat.map((msg, i) => (
          <div
            key={i}
            className={`mb-2 ${msg.role === "user" ? "text-blue-600" : msg.role === "assistant" ? "text-green-600" : "text-gray-600"}`}
          >
            <b>{msg.role}:</b> {msg.content}
          </div>
        ))}
      </div>

      <div className="mt-4 flex gap-2">
        <input
          value={message}
          onChange={e => setMessage(e.target.value)}
          className="border flex-1 p-2 rounded"
          placeholder="Type your message..."
        />
        <button
          onClick={sendMessage}
          className="bg-black text-white px-4 py-2 rounded"
        >
          Send
        </button>
      </div>
    </div>
  )
}
