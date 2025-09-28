const injected =
  typeof window !== "undefined" &&
  (window as any).rapidagent &&
  (window as any).rapidagent.apiBase

const BASE =
  injected || import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"

export async function api<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, opts)
  if (!res.ok) throw new Error(`API ${path} failed: ${res.status}`)
  return res.json()
}
