import { useEffect, useState, useRef } from "react"
import { api } from "../lib/api"
import { Card, ScrollArea, Textarea, Button, Select, Stack, Group, Text } from "@mantine/core"

interface Agent {
  id: string
  name: string
  model: string
  status: string
}

interface AgentDetails {
  agent: Agent
  tools: string[]
  messages: { role: string; content: string; timestamp?: string }[]
}

export default function ChatPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [selectedAgent, setSelectedAgent] = useState<string>("")
  const [chat, setChat] = useState<{ role: string; content: string }[]>([])
  const [message, setMessage] = useState("")
  const viewport = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api<{ agents: Agent[] }>("/agents").then(data => {
      setAgents(data.agents)
      if (data.agents.length > 0) setSelectedAgent(data.agents[0].id)
    })
  }, [])

  useEffect(() => {
    if (selectedAgent) {
      api<AgentDetails>(`/agents/${selectedAgent}`).then(data => {
        setChat(data.messages || [])
      })
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
    setTimeout(() => viewport.current?.scrollTo({ top: viewport.current.scrollHeight, behavior: "smooth" }), 100)
  }

  return (
    <Stack spacing="md" h="100%">
      <Select
        label="Select agent"
        value={selectedAgent}
        onChange={val => setSelectedAgent(val || "")}
        data={agents.map(a => ({ value: a.id, label: `${a.name} (${a.model}) – ${a.status}` }))}
      />

      <Card withBorder shadow="sm" className="flex-1 flex flex-col">
        <ScrollArea style={{ flex: 1 }} viewportRef={viewport}>
          <Stack spacing="xs" p="md">
            {chat.map((msg, i) => (
              <Group
                key={i}
                position={msg.role === "user" ? "right" : "left"}
              >
                <Card
                  shadow="sm"
                  radius="md"
                  p="sm"
                  style={{
                    backgroundColor: msg.role === "user" ? "var(--mantine-color-blue-6)" : "var(--mantine-color-gray-2)",
                    color: msg.role === "user" ? "white" : "black",
                    maxWidth: "75%",
                  }}
                >
                  <Text size="sm">{msg.content}</Text>
                </Card>
              </Group>
            ))}
          </Stack>
        </ScrollArea>

        <Group p="sm" spacing="sm" style={{ borderTop: "1px solid var(--mantine-color-gray-3)" }}>
          <Textarea
            value={message}
            onChange={e => setMessage(e.currentTarget.value)}
            placeholder="Type your message..."
            minRows={1}
            autosize
            style={{ flex: 1 }}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && sendMessage()}
          />
          <Button onClick={sendMessage}>Send</Button>
        </Group>
      </Card>
    </Stack>
  )
}
