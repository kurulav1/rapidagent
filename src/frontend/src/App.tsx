import { Routes, Route, Link } from "react-router-dom"
import ChatPage from "./pages/ChatPage"
import AgentsPage from "./pages/AgentsPage"
import AgentMonitorPage from "./pages/AgentMonitorPage"
import MonitorPage from "./pages/MonitorPage"

export default function App() {
  return (
    <div className="flex h-screen">
      <aside className="w-64 bg-gray-100 border-r p-4 flex flex-col">
        <h1 className="text-xl font-bold mb-6">RapidAgent</h1>
        <nav className="space-y-2 flex-1">
          <Link to="/chat" className="block px-2 py-1 hover:bg-gray-200 rounded">
            Chat
          </Link>
          <Link to="/agents" className="block px-2 py-1 hover:bg-gray-200 rounded">
            Agents
          </Link>
          <Link to="/monitor" className="block px-2 py-1 hover:bg-gray-200 rounded">
            Monitor
          </Link>
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/agents" element={<AgentsPage />} />
          <Route path="/monitor" element={<MonitorPage />} />
          <Route path="/monitor/:agentId" element={<AgentMonitorPage />} />
          <Route path="*" element={<ChatPage />} />
        </Routes>
      </main>
    </div>
  )
}
