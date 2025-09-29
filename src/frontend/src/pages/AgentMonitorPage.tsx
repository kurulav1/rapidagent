import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { api } from "../lib/api"
import { Card, Text, Badge, Modal, Group, Button } from "@mantine/core"

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
  content: any
}

export default function AgentMonitorPage() {
  const { agentId } = useParams<{ agentId: string }>()
  const [agent, setAgent] = useState<Agent | null>(null)
  const [traces, setTraces] = useState<Trace[]>([])
  const [loading, setLoading] = useState(true)
  const [opened, setOpened] = useState(false)
  const [toolDetails, setToolDetails] = useState<any>(null)

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

      <Card shadow="sm" padding="lg" radius="md" withBorder>
        <Text fw={700} size="lg">{agent.name}</Text>
        <Text size="sm" c="dimmed">
          Model: {agent.model} • Status:{" "}
          <Badge color={
            agent.status === "idle" ? "green" :
            agent.status === "running" ? "blue" : "red"
          }>
            {agent.status}
          </Badge>
        </Text>
        <Text size="xs" c="dimmed">
          Created: {new Date(agent.created_at).toLocaleString()} • Last seen:{" "}
          {agent.last_seen ? new Date(agent.last_seen).toLocaleString() : "–"}
        </Text>
      </Card>

      <div>
        <Text fw={600} mb="sm">Trace</Text>
        {traces.length === 0 ? (
          <Text size="sm" c="dimmed">No traces yet</Text>
        ) : (
          <div className="space-y-2">
            {traces.map((t, i) => (
              <Card key={i} padding="sm" withBorder radius="md">
                <Text size="xs" c="dimmed">
                  {new Date(t.timestamp).toLocaleTimeString()}
                </Text>
                {t.type === "action" && typeof t.content === "object" ? (
                  <Button
                    variant="subtle"
                    color="blue"
                    onClick={() => { setToolDetails(t.content); setOpened(true) }}
                  >
                    🔧 Action: {t.content.tool}
                  </Button>
                ) : t.type === "observation" && typeof t.content === "object" ? (
                  <Text size="sm">Observation: {t.content.output}</Text>
                ) : (
                  <Text size="sm">{t.type}: {typeof t.content === "string" ? t.content : JSON.stringify(t.content)}</Text>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>

      <Modal opened={opened} onClose={() => setOpened(false)} title="Tool Details">
        {toolDetails && (
          <div>
            <Text><b>Tool:</b> {toolDetails.tool}</Text>
            {"input" in toolDetails && <Text><b>Input:</b> {toolDetails.input}</Text>}
            {"output" in toolDetails && <Text><b>Output:</b> {toolDetails.output}</Text>}
          </div>
        )}
      </Modal>
    </div>
  )
}
