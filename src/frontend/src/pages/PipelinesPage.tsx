import { useEffect, useState, useCallback } from "react"
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  Edge,
  Node,
  NodeChange,
  EdgeChange,
  applyNodeChanges,
  applyEdgeChanges,
  Handle,
  Position,
  ReactFlowProvider,
  useReactFlow,
} from "reactflow"
import "reactflow/dist/style.css"
import {
  Card,
  Text,
  Title,
  Loader,
  Alert,
  Button,
  Group,
  Stack,
  Badge,
} from "@mantine/core"
import { api } from "../lib/api"

interface Tool {
  name: string
  description: string
  type: string
  config?: {
    input_schema?: Record<string, any>
    output_schema?: Record<string, any>
  }
}

function ToolNode({ data }: { data: any }) {
  return (
    <Card shadow="sm" p="sm" radius="md" withBorder style={{ minWidth: 200 }}>
      <Group justify="space-between" mb="xs">
        <Title order={5}>{data.label}</Title>
        <Badge size="sm" color="blue">
          {data.type}
        </Badge>
      </Group>
      <Text size="xs" c="dimmed" lineClamp={2} mb="xs">
        {data.description}
      </Text>
      {data.inputs?.length > 0 && (
        <Stack gap={2} mb="xs">
          <Text size="xs" fw={500}>
            Inputs:
          </Text>
          {data.inputs.map((i: any, idx: number) => (
            <Text size="xs" key={idx}>
              • {i.name} ({i.type})
            </Text>
          ))}
        </Stack>
      )}
      {data.outputs?.length > 0 && (
        <Stack gap={2}>
          <Text size="xs" fw={500}>
            Outputs:
          </Text>
          {data.outputs.map((o: any, idx: number) => (
            <Text size="xs" key={idx}>
              • {o.name} ({o.type})
            </Text>
          ))}
        </Stack>
      )}
      <Handle type="target" position={Position.Left} isConnectable />
      <Handle type="source" position={Position.Right} isConnectable />
    </Card>
  )
}

const nodeTypes = { tool: ToolNode }

function PipelineEditor() {
  const [tools, setTools] = useState<Tool[]>([])
  const [nodes, setNodes] = useState<Node[]>([])
  const [edges, setEdges] = useState<Edge[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const { deleteElements, setNodes: setFlowNodes, setEdges: setFlowEdges } =
    useReactFlow()

  // load data once on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        const toolData = await api<{ tools: Tool[] }>("/tools")
        setTools(toolData.tools)
        try {
          const pipelineData = await api<{ nodes: Node[]; edges: Edge[] }>(
            "/pipelines"
          )
          if (pipelineData.nodes) {
            setNodes(pipelineData.nodes)
            setFlowNodes(pipelineData.nodes)
          }
          if (pipelineData.edges) {
            setEdges(pipelineData.edges)
            setFlowEdges(pipelineData.edges)
          }
        } catch {
          /* no saved pipeline yet */
        }
      } catch (err: any) {
        setError(err.message)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [setFlowNodes, setFlowEdges])

  // delete handler
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Delete" || e.key === "Backspace") {
        deleteElements({ nodes, edges })
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [deleteElements, nodes, edges])

  const addToolNode = (tool: Tool) => {
    const newNode: Node = {
      id: `${tool.name}-${nodes.length}`,
      type: "tool",
      position: { x: 150 + nodes.length * 60, y: 100 + nodes.length * 40 },
      data: {
        label: tool.name,
        description: tool.description,
        type: tool.type,
        inputs: tool.config?.input_schema
          ? Object.entries(tool.config.input_schema).map(([k, v]) => ({
              name: k,
              ...(v as any),
            }))
          : [],
        outputs: tool.config?.output_schema
          ? Object.entries(tool.config.output_schema).map(([k, v]) => ({
              name: k,
              ...(v as any),
            }))
          : [],
      },
    }
    setNodes((nds) => [...nds, newNode])
    setFlowNodes((nds) => [...nds, newNode])
  }

  const onConnect = useCallback(
    (params: Connection) =>
      setEdges((eds) =>
        addEdge(
          {
            ...params,
            animated: true,
            style: { strokeWidth: 2 },
          },
          eds
        )
      ),
    []
  )

  const onNodesChange = useCallback(
    (changes: NodeChange[]) =>
      setNodes((nds) => applyNodeChanges(changes, nds)),
    []
  )

  const onEdgesChange = useCallback(
    (changes: EdgeChange[]) =>
      setEdges((eds) => applyEdgeChanges(changes, eds)),
    []
  )

  const savePipeline = async () => {
    setSaving(true)
    try {
      await api("/pipelines", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ nodes, edges }),
      })
      alert("Pipeline saved!")
    } catch (err: any) {
      alert(`Failed to save: ${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <Loader />
  if (error) return <Alert color="red">{error}</Alert>

  return (
    <Group align="flex-start" p="md" gap="lg">
      {/* Sidebar */}
      <Card withBorder shadow="sm" p="md" style={{ width: 300 }}>
        <Title order={4} mb="sm">
          Add Tools
        </Title>
        {tools.length === 0 ? (
          <Text c="dimmed">No tools available. Create some in the Tools page.</Text>
        ) : (
          <Stack>
            {tools.map((tool) => (
              <Card
                key={tool.name}
                shadow="xs"
                withBorder
                p="sm"
                style={{ cursor: "pointer" }}
                onClick={() => addToolNode(tool)}
              >
                <Group justify="space-between" mb="xs">
                  <Text fw={500}>{tool.name}</Text>
                  <Badge size="sm">{tool.type}</Badge>
                </Group>
                <Text size="xs" c="dimmed" lineClamp={2}>
                  {tool.description}
                </Text>
                <Button mt="xs" fullWidth variant="light" size="xs">
                  + Add
                </Button>
              </Card>
            ))}
          </Stack>
        )}
        <Button
          mt="lg"
          fullWidth
          disabled={nodes.length === 0 || saving}
          onClick={savePipeline}
        >
          {saving ? "Saving..." : "Save Pipeline"}
        </Button>
        <Text size="xs" c="dimmed" mt="sm">
          Tip: Select a node or edge and press Delete to remove it.
        </Text>
      </Card>

      {/* Canvas */}
      <div
        style={{
          flex: 1,
          height: "85vh",
          border: "1px solid var(--mantine-color-gray-4)",
          borderRadius: "8px",
          overflow: "hidden",
          boxShadow: "0 2px 6px rgba(0,0,0,0.1)",
        }}
      >
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background gap={16} size={1} color="#aaa" />
          <MiniMap />
          <Controls />
        </ReactFlow>
      </div>
    </Group>
  )
}

export default function PipelinesPage() {
  return (
    <ReactFlowProvider>
      <PipelineEditor />
    </ReactFlowProvider>
  )
}
