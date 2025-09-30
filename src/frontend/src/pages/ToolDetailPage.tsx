import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { Title, Text, Card, Loader, Alert, Stack } from "@mantine/core"
import { api } from "../lib/api"

interface Trace {
  timestamp: string
  type: string
  content: any
}

export default function ToolDetailPage() {
  const { agentId, toolName } = useParams<{ agentId: string; toolName: string }>()
  const [traces, setTraces] = useState<Trace[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!agentId) return

    api<{ traces: Trace[] }>(`/agents/${agentId}/traces`)
      .then(data => {
        const filtered = data.traces.filter(
          t =>
            (t.type === "action" && t.content.tool === toolName) ||
            (t.type === "observation" && t.content.tool === toolName)
        )
        setTraces(filtered)
        setLoading(false)
      })
      .catch(err => {
        setError(err.message)
        setLoading(false)
      })
  }, [agentId, toolName])

  if (loading) return <Loader />
  if (error) return <Alert color="red">{error}</Alert>

  return (
    <Stack>
      <Link to={`/monitor/${agentId}`}>&larr; Back to Agent</Link>
      <Title order={2}>Tool: {toolName}</Title>
      {traces.length === 0 ? (
        <Text c="dimmed">No runs for this tool yet.</Text>
      ) : (
        traces.map((t, i) => (
          <Card key={i} withBorder shadow="sm">
            <Text size="sm" c="dimmed">
              {new Date(t.timestamp).toLocaleString()}
            </Text>
            <Text fw={500}>{t.type}</Text>
            <pre
              style={{
                background: "#f5f5f5",
                padding: "8px",
                borderRadius: "4px",
                marginTop: "4px",
                overflowX: "auto",
              }}
            >
              {JSON.stringify(t.content, null, 2)}
            </pre>
          </Card>
        ))
      )}
    </Stack>
  )
}
