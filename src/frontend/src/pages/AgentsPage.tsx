import { useEffect, useState } from "react"
import { api } from "../lib/api"
import {
  Button,
  Card,
  Checkbox,
  Group,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from "@mantine/core"

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
      body: JSON.stringify({ name, model, tools: selectedTools }),
    })
    setName("")
    setSelectedTools([])
    await refreshAgents()
  }

  return (
    <Stack p="md">
      <Title order={2}>Agents</Title>

      <Card withBorder shadow="sm" p="md">
        <Stack>
          <Title order={4}>Create Agent</Title>
          <Group>
            <TextInput
              placeholder="Agent name"
              value={name}
              onChange={e => setName(e.currentTarget.value)}
              style={{ flex: 1 }}
            />
            <Select
              data={models}
              value={model}
              onChange={val => setModel(val || "")}
              placeholder="Select model"
              style={{ flex: 1 }}
            />
          </Group>

          <Stack gap="xs">
            <Text fw={500} size="sm">
              Assign Tools
            </Text>
            {tools.map(tool => (
              <Checkbox
                key={tool.name}
                label={`${tool.name} – ${tool.description}`}
                checked={selectedTools.includes(tool.name)}
                onChange={() => toggleTool(tool.name)}
              />
            ))}
          </Stack>

          <Button onClick={createAgent}>Create</Button>
        </Stack>
      </Card>

      <Title order={4}>Existing Agents</Title>
      {agents.length === 0 ? (
        <Text c="dimmed" size="sm">
          No agents yet
        </Text>
      ) : (
        <Table striped highlightOnHover withBorder withColumnBorders>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Model</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Tools</Table.Th>
              <Table.Th>Created</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {agents.map(agent => (
              <Table.Tr key={agent.id}>
                <Table.Td>{agent.name}</Table.Td>
                <Table.Td>{agent.model}</Table.Td>
                <Table.Td>{agent.status}</Table.Td>
                <Table.Td>
                  {agent.tools && agent.tools.length > 0
                    ? agent.tools.join(", ")
                    : "None"}
                </Table.Td>
                <Table.Td>
                  {agent.created_at
                    ? new Date(agent.created_at).toLocaleString()
                    : "Unknown"}
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  )
}
