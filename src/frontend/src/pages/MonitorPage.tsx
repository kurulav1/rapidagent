import { useEffect, useState } from "react"
import { Link } from "react-router-dom"
import { api } from "../lib/api"
import {
  Badge,
  Card,
  Group,
  Loader,
  Stack,
  Text,
  Title,
} from "@mantine/core"

interface Agent {
  id: string
  name: string
  model: string
  status: string
  created_at: string
}

export default function MonitorPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAgents = () => {
      api<{ agents: Agent[] }>("/agents")
        .then(data => setAgents(data.agents))
        .catch(err => console.error("Failed to load agents", err))
        .finally(() => setLoading(false))
    }
    fetchAgents()
    const interval = setInterval(fetchAgents, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return <Loader m="lg" />

  return (
    <Stack p="md" gap="md">
      <Title order={2}>Agent Monitor</Title>
      {agents.length === 0 ? (
        <Text c="dimmed">No agents detected</Text>
      ) : (
        <Stack gap="sm">
          {agents.map(agent => (
            <Card
              key={agent.id}
              withBorder
              shadow="sm"
              component={Link}
              to={`/monitor/${agent.id}`}
              style={{ textDecoration: "none" }}
            >
              <Group justify="space-between">
                <Stack gap={2}>
                  <Text fw={500}>{agent.name}</Text>
                  <Text size="sm" c="dimmed">
                    Model: {agent.model}
                  </Text>
                  <Text size="xs" c="dimmed">
                    Created: {new Date(agent.created_at).toLocaleString()}
                  </Text>
                </Stack>
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
            </Card>
          ))}
        </Stack>
      )}
    </Stack>
  )
}
