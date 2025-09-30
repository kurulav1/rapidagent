import { Routes, Route, Link } from "react-router-dom";
import {
  AppShell,
  Button,
  Group,
  ScrollArea,
  useMantineColorScheme,
} from "@mantine/core";
import {
  IconUsers,
  IconMessageCircle,
  IconKey,
  IconActivity,
  IconTool,
  IconSun,
  IconMoonStars,
} from "@tabler/icons-react";
import AgentsPage from "./pages/AgentsPage";
import MonitorPage from "./pages/MonitorPage";
import AgentMonitorPage from "./pages/AgentMonitorPage";
import ChatPage from "./pages/ChatPage";
import ToolsPage from "./pages/ToolsPage";
import KeysPage from "./pages/KeysPage";
import ToolDetailPage from "./pages/ToolDetailPage";

function Sidebar() {
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <ScrollArea style={{ flex: 1 }}>
        <Group direction="column" gap="xs" p="xs">
          <Button
            component={Link}
            to="/"
            variant="subtle"
            fullWidth
            leftSection={<IconUsers size={16} />}
          >
            Agents
          </Button>
          <Button
            component={Link}
            to="/monitor"
            variant="subtle"
            fullWidth
            leftSection={<IconActivity size={16} />}
          >
            Monitor
          </Button>
          <Button
            component={Link}
            to="/chat"
            variant="subtle"
            fullWidth
            leftSection={<IconMessageCircle size={16} />}
          >
            Chat
          </Button>
          <Button
            component={Link}
            to="/tools"
            variant="subtle"
            fullWidth
            leftSection={<IconTool size={16} />}
          >
            Tools
          </Button>
          <Button
            component={Link}
            to="/keys"
            variant="subtle"
            fullWidth
            leftSection={<IconKey size={16} />}
          >
            API Keys
          </Button>
        </Group>
      </ScrollArea>
      <div style={{ padding: "8px" }}>
        <Button
          variant="light"
          color="gray"
          fullWidth
          onClick={() => toggleColorScheme()}
          leftSection={
            colorScheme === "dark" ? (
              <IconSun size={16} />
            ) : (
              <IconMoonStars size={16} />
            )
          }
        >
          {colorScheme === "dark" ? "Light Mode" : "Dark Mode"}
        </Button>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AppShell
      padding="md"
      navbar={{ width: 240, breakpoint: "sm", collapsed: { mobile: false } }}
    >
      <AppShell.Navbar>
        <Sidebar />
      </AppShell.Navbar>

      <AppShell.Main>
        <Routes>
          <Route path="/" element={<AgentsPage />} />
          <Route path="/monitor" element={<MonitorPage />} />
          <Route path="/monitor/:agentId" element={<AgentMonitorPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/tools" element={<ToolsPage />} />
          <Route path="/keys" element={<KeysPage />} />
          <Route path="/monitor/:agentId/tools/:toolName" element={<ToolDetailPage />} />
        </Routes>
      </AppShell.Main>
    </AppShell>
  );
}
