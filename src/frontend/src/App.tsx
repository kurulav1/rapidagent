import { Routes, Route, Link } from "react-router-dom"
import { AppShell, Group, Button, Stack } from "@mantine/core"
import { IconUsers, IconMessageCircle, IconKey, IconActivity, IconSun, IconMoonStars } from "@tabler/icons-react"
import { useMantineColorScheme, ActionIcon } from "@mantine/core"

import AgentsPage from "./pages/AgentsPage"
import MonitorPage from "./pages/MonitorPage"
import AgentMonitorPage from "./pages/AgentMonitorPage"
import ChatPage from "./pages/ChatPage"
import KeysPage from "./pages/KeysPage"

export default function App() {
  return (
    <AppShell
      padding="md"
      header={{ height: 50 }}
      navbar={{ width: 220, breakpoint: "sm" }}
    >
      {/* Header */}
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <div style={{ fontWeight: 700 }}>RapidAgent</div>
        </Group>
      </AppShell.Header>

      {/* Sidebar */}
      <AppShell.Navbar p="xs">
        <Stack gap="sm">
          <NavItem to="/" icon={<IconUsers size={16} />}>Agents</NavItem>
          <NavItem to="/monitor" icon={<IconActivity size={16} />}>Monitor</NavItem>
          <NavItem to="/chat" icon={<IconMessageCircle size={16} />}>Chat</NavItem>
          <NavItem to="/keys" icon={<IconKey size={16} />}>Keys</NavItem>

          {/* Push dark mode toggle to bottom */}
          <div style={{ flex: 1 }} />
          <ColorSchemeToggle />
        </Stack>
      </AppShell.Navbar>

      {/* Main content */}
      <AppShell.Main>
        <Routes>
          <Route path="/" element={<AgentsPage />} />
          <Route path="/monitor" element={<MonitorPage />} />
          <Route path="/monitor/:agentId" element={<AgentMonitorPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/chat/:agentId" element={<ChatPage />} />
          <Route path="/keys" element={<KeysPage />} />
        </Routes>
      </AppShell.Main>
    </AppShell>
  )
}

function NavItem({ to, icon, children }: { to: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Button
      component={Link}
      to={to}
      variant="subtle"
      fullWidth
      leftSection={icon}
      styles={{ inner: { justifyContent: "flex-start" } }}
    >
      {children}
    </Button>
  )
}

function ColorSchemeToggle() {
  const { colorScheme, setColorScheme } = useMantineColorScheme()
  const dark = colorScheme === "dark"

  return (
    <ActionIcon
      variant="light"
      onClick={() => setColorScheme(dark ? "light" : "dark")}
      title="Toggle color scheme"
    >
      {dark ? <IconSun size={18} /> : <IconMoonStars size={18} />}
    </ActionIcon>
  )
}
