import React, { useEffect, useState } from "react"

export default function App() {
  const [health, setHealth] = useState("checking...")
  const [message, setMessage] = useState("")
  const [reply, setReply] = useState("")

  useEffect(() => {
    fetch("http://localhost:8000/health")
      .then(r => r.json())
      .then(() => setHealth("ok"))
      .catch(() => setHealth("unavailable"))
  }, [])

  const send = async () => {
    const res = await fetch("http://localhost:8000/requests/chat", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        messages: [{ role: "user", content: message }]
      })
    })
    const data = await res.json()
    setReply(data.messages[data.messages.length - 1].content)
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold">Quick Agentic Console</h1>
      <p className="mt-2">Backend health: {health}</p>
      <div className="mt-4 flex gap-2">
        <input
          value={message}
          onChange={e => setMessage(e.target.value)}
          className="border p-2 rounded flex-1"
        />
        <button onClick={send} className="bg-black text-white px-4 py-2 rounded">
          Send
        </button>
      </div>
      {reply && <p className="mt-4 p-2 border rounded">Reply: {reply}</p>}
    </div>
  )
}
