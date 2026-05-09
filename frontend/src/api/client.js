const BASE = '/api'

export async function sendChat(message, history = []) {
  const res = await fetch(`${BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, history }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export async function fetchExamples() {
  const res = await fetch(`${BASE}/chat/examples`)
  return res.json()
}

export async function fetchAnalytics(endpoint) {
  const res = await fetch(`${BASE}/analytics/${endpoint}`)
  if (!res.ok) throw new Error(`Analytics error: ${res.status}`)
  return res.json()
}

export async function checkHealth() {
  try {
    const res = await fetch(`${BASE.replace('/api','')}//health`.replace('///','//'))
    const r = await fetch('/health')
    return r.ok ? r.json() : null
  } catch { return null }
}
