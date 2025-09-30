import { useEffect, useState } from "react"
import {
  Card,
  Text,
  Title,
  SimpleGrid,
  Loader,
  Alert,
  Button,
  Stack,
  TextInput,
  Select,
  Group,
} from "@mantine/core"
import { IconTool, IconTrash } from "@tabler/icons-react"
import Editor from "@monaco-editor/react"
import { api } from "../lib/api"

interface Tool {
  name: string
  description: string
  type: string
  config?: Record<string, any>
  inputs?: { name: string; type: string; description: string }[]
  outputs?: { name: string; type: string; description: string }[]
}

export default function ToolsPage() {
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [type, setType] = useState("")
  const [code, setCode] = useState("")

  const [inputs, setInputs] = useState([{ name: "input", type: "string", description: "" }])
  const [outputs, setOutputs] = useState([{ name: "output", type: "string", description: "" }])

  const [httpConfig, setHttpConfig] = useState("")

  const loadTools = async () => {
    setLoading(true)
    try {
      const data = await api<{ tools: Tool[] }>("/tools")
      setTools(data.tools)
      setLoading(false)
    } catch (err: any) {
      setError(err.message)
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTools()
  }, [])

  const scaffoldCode = (ins = inputs, outs = outputs) => {
    const argList = ins.map(i => `${i.name}: ${mapType(i.type)}`).join(", ") || "input: str"
    const argsDoc = ins.map(i => `        ${i.name} (${mapType(i.type)}): ${i.description || ""}`).join("\n")
    const retDoc = outs.map(o => `        ${o.name}: ${mapType(o.type)} – ${o.description || ""}`).join("\n")
    const retDict = `{ ${outs.map(o => `"${o.name}": ""`).join(", ")} }` || "{}"

    return `def run(${argList}):
    """
    Args:
${argsDoc || "        input (str): input value"}
    Returns:
        dict
${retDoc ? "\n" + retDoc : ""}
    """
    # TODO: implement your logic here
    return ${retDict}
`
  }

  const mapType = (t: string) => {
    if (t === "number") return "int"
    if (t === "object") return "dict"
    return "str"
  }

  const updateInput = (i: number, field: string, value: string) => {
    setInputs(prev => {
      const copy = [...prev]
      ;(copy[i] as any)[field] = value
      return copy
    })
    setCode(scaffoldCode())
  }

  const updateOutput = (i: number, field: string, value: string) => {
    setOutputs(prev => {
      const copy = [...prev]
      ;(copy[i] as any)[field] = value
      return copy
    })
    setCode(scaffoldCode())
  }

  const createTool = async () => {
    let config: any = {}
    if (type === "http") {
      config = httpConfig ? JSON.parse(httpConfig) : {}
    }
    if (type === "python") {
      config = {
        code,
        inputs,
        outputs,
      }
    }
    try {
      await api("/tools", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          name,
          description,
          type,
          config,
        }),
      })
      setName("")
      setDescription("")
      setType("")
      setCode("")
      setInputs([{ name: "input", type: "string", description: "" }])
      setOutputs([{ name: "output", type: "string", description: "" }])
      setHttpConfig("")
      loadTools()
    } catch (err: any) {
      alert(`Failed to create tool: ${err.message}`)
    }
  }

  const deleteTool = async (toolName: string) => {
    if (!window.confirm(`Delete tool "${toolName}"?`)) return
    await api(`/tools/${toolName}`, { method: "DELETE" })
    loadTools()
  }

  if (loading) return <Loader />
  if (error) return <Alert color="red">{error}</Alert>

  return (
    <div>
      <Title order={2} mb="md">
        Tools
      </Title>

      <Card withBorder shadow="sm" p="md" mb="lg">
        <Stack>
          <Title order={4}>Create Tool</Title>
          <TextInput placeholder="Tool name" value={name} onChange={e => setName(e.currentTarget.value)} />
          <TextInput placeholder="Description" value={description} onChange={e => setDescription(e.currentTarget.value)} />
          <Select data={["calculator", "search", "http", "python"]} value={type} onChange={val => setType(val || "")} placeholder="Select type" />
          {type === "http" && (
            <TextInput value={httpConfig} onChange={e => setHttpConfig(e.currentTarget.value)} placeholder='{"method":"GET","url":"https://api.example.com?q={query}","headers":{}}' />
          )}
          {type === "python" && (
            <Stack>
              <Title order={5}>Inputs</Title>
              {inputs.map((inp, i) => (
                <Group key={i} grow>
                  <TextInput placeholder="Name" value={inp.name} onChange={e => updateInput(i, "name", e.currentTarget.value)} />
                  <Select data={["string", "number", "object"]} value={inp.type} onChange={val => updateInput(i, "type", val || "string")} />
                  <TextInput placeholder="Description" value={inp.description} onChange={e => updateInput(i, "description", e.currentTarget.value)} />
                </Group>
              ))}
              <Button variant="light" onClick={() => setInputs([...inputs, { name: "", type: "string", description: "" }])}>+ Add Input</Button>

              <Title order={5}>Outputs</Title>
              {outputs.map((out, i) => (
                <Group key={i} grow>
                  <TextInput placeholder="Name" value={out.name} onChange={e => updateOutput(i, "name", e.currentTarget.value)} />
                  <Select data={["string", "number", "object"]} value={out.type} onChange={val => updateOutput(i, "type", val || "string")} />
                  <TextInput placeholder="Description" value={out.description} onChange={e => updateOutput(i, "description", e.currentTarget.value)} />
                </Group>
              ))}
              <Button variant="light" onClick={() => setOutputs([...outputs, { name: "", type: "string", description: "" }])}>+ Add Output</Button>

              <Title order={5}>Code</Title>
              <Editor
                height="220px"
                defaultLanguage="python"
                theme="vs-dark"
                value={code || scaffoldCode()}
                onChange={(val) => setCode(val || "")}
              />
            </Stack>
          )}
          <Button onClick={createTool} disabled={!name || !type}>Save</Button>
        </Stack>
      </Card>

      {tools.length === 0 ? (
        <Text c="dimmed">No tools registered.</Text>
      ) : (
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
          {tools.map(tool => (
            <Card key={tool.name} shadow="sm" p="lg" radius="md" withBorder>
              <Group justify="space-between" align="flex-start">
                <div>
                  <IconTool size={28} />
                  <Title order={4} mt="sm">{tool.name}</Title>
                  <Text c="dimmed" size="sm" mt="xs">{tool.description}</Text>
                  <Text size="xs" mt="xs">Type: {tool.type}</Text>
                  {tool.inputs && <pre>{JSON.stringify(tool.inputs, null, 2)}</pre>}
                  {tool.outputs && <pre>{JSON.stringify(tool.outputs, null, 2)}</pre>}
                </div>
                <Button color="red" variant="light" onClick={() => deleteTool(tool.name)}>
                  <IconTrash size={16} />
                </Button>
              </Group>
            </Card>
          ))}
        </SimpleGrid>
      )}
    </div>
  )
}
