import React, { useState, useEffect } from "react"

export default function KeysPage() {
  const [openaiKey, setOpenaiKey] = useState("")

  useEffect(() => {
    const saved = localStorage.getItem("OPENAI_API_KEY") || ""
    setOpenaiKey(saved)
  }, [])

  const save = () => {
    localStorage.setItem("OPENAI_API_KEY", openaiKey)
    alert("Saved locally (frontend only). Backend still uses environment vars.")
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-bold mb-4">API Keys</h2>

      <div className="mb-4">
        <label className="block font-semibold">OpenAI API Key</label>
        <input
          type="password"
          value={openaiKey}
          onChange={e => setOpenaiKey(e.target.value)}
          className="border p-2 rounded w-full mt-1"
          placeholder="sk-..."
        />
      </div>

      <button
        onClick={save}
        className="bg-black text-white px-4 py-2 rounded"
      >
        Save
      </button>
    </div>
  )
}
