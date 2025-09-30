import { useEffect, useState } from "react"
import { useParams, Link } from "react-router-dom"
import { api } from "../lib/api"
import {
  Card,
  Text,
  Title,
  Group,
  Stack,
  Badge,
  Loader,
  Button,
} from "@mantine/core"

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

  useEffect(() => {
    if (!agentId) return

    const fetchData = () => {
      api<{ agent: Agent }>(`/agents/${agentId}`)
        .then((data) => setAgent(data.agent))
        .catch(() => setAgent(null))

      api<{ traces: Trace[] }>(`/agents/${agentId}/traces`)
        .then((data) => setTraces(data.traces))
        .catch(() => setTraces([]))

      setLoading(false)
    }

    fetchData()
    const interval = setInterval(fetchData, 5000)
    return () => clearInterval(interval)
  }, [agentId])

  if (loading) return <Loader m="xl" />
  if (!agent) return <Text p="md">Agent not found.</Text>

  const renderContent = (content: any) => {
    if (typeof content === "string") return content
    try {
      return <pre style={{ margin: 0 }}>{JSON.stringify(content, null, 2)}</pre>
    } catch {
      return String(content)
    }
  }

  return (
    <Stack p="md" spacing="lg">
      <Group>
        <Link to="/monitor">
          <Button variant="subtle" size="xs">
            ← Back to monitor list
          </Button>
        </Link>
      </Group>

      <Card withBorder shadow="sm">
        <Title order={2}>{agent.name}</Title>
        <Group spacing="xs" mt="xs">
          <Text size="sm" c="dimmed">
            Model: {agent.model} • Status:
          </Text>
          <Badge
            color={
              agent.status === "idle"
                ? "green"
                : agent.status === "running"
                ? "blue"
                : "red"
            }
          >
            {agent.status}
          </Badge>
        </Group>
        <Text size="xs" c="dimmed" mt="xs">
          Created: {new Date(agent.created_at).toLocaleString()} • Last seen:{" "}
          {agent.last_seen ? new Date(agent.last_seen).toLocaleString() : "–"}
        </Text>
      </Card>

      <Stack spacing="sm">
        <Title order={4}>Trace</Title>
        {traces.length === 0 ? (
          <Text size="sm" c="dimmed">
            No traces yet
          </Text>
        ) : (
          traces.map((t, i) => {
            const ts = new Date(t.timestamp).toLocaleTimeString()
            if (t.type === "thought") {
              return (
                <Card key={i} withBorder padding="sm" shadow="xs">
                  <Group>
                    <Badge color="gray">Thought</Badge>
                    <Text size="xs" c="dimmed">
                      {ts}
                    </Text>
                  </Group>
                  {renderContent(t.content)}
                </Card>
              )
            }
            if (t.type === "action") {
              return (
                <Card key={i} withBorder padding="sm" shadow="xs">
                  <Group position="apart">
                    <Group>
                      <Badge color="blue">Action</Badge>
                      <Text size="xs" c="dimmed">
                        {ts}
                      </Text>
                    </Group>
                    <Link to={`/monitor/${agentId}/tools/${t.content.tool}`}>
                      <Button size="xs" variant="light">
                        View runs
                      </Button>
                    </Link>
                  </Group>
                  <Text>
                    <b>Tool:</b> {t.content.tool}
                  </Text>
                  <Text>
                    <b>Input:</b> {t.content.input}
                  </Text>
                </Card>
              )
            }
            if (t.type === "observation") {
              return (
                <Card key={i} withBorder padding="sm" shadow="xs">
                  <Group>
                    <Badge color="teal">Observation</Badge>
                    <Text size="xs" c="dimmed">
                      {ts}
                    </Text>
                  </Group>
                  <Text>
                    <b>Tool:</b> {t.content.tool}
                  </Text>
                  <Text>
                    <b>Output:</b> {renderContent(t.content.output)}
                  </Text>
                </Card>
              )
            }
            if (t.type === "final") {
              return (
                <Card key={i} withBorder padding="sm" shadow="xs">
                  <Group>
                    <Badge color="violet">Final</Badge>
                    <Text size="xs" c="dimmed">
                      {ts}
                    </Text>
                  </Group>
                  {renderContent(t.content)}
                </Card>
              )
            }
            return null
          })
        )}
      </Stack>
    </Stack>
  )
}
