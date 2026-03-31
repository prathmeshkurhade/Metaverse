/**
 * Simple API helper for making authenticated requests.
 *
 * WHY a custom hook instead of just fetch()?
 * Every API call needs the JWT token in the Authorization header.
 * Without this helper, every component would repeat the token logic.
 * DRY -- write the boilerplate once.
 */

// In dev, Vite proxy handles routing. In prod, Nginx handles it.
// So we use relative URLs (/api/v1/...) which work in both cases.
const API_BASE = '/api/v1'
const AI_BASE = '/api/v1/ai'

function getToken() {
  return localStorage.getItem('token')
}

function getHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export const api = {
  // ─── Auth ───
  async signup(username, password, type = 'user') {
    const res = await fetch(`${API_BASE}/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password, type }),
    })
    return res.json()
  },

  async signin(username, password) {
    const res = await fetch(`${API_BASE}/signin`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })
    if (!res.ok) throw new Error('Invalid credentials')
    const data = await res.json()
    localStorage.setItem('token', data.token)
    return data
  },

  // ─── Spaces ───
  async listSpaces() {
    const res = await fetch(`${API_BASE}/space/all`, { headers: getHeaders() })
    return res.json()
  },

  async createSpace(name, dimensions) {
    const res = await fetch(`${API_BASE}/space`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ name, dimensions }),
    })
    return res.json()
  },

  async getSpace(spaceId) {
    const res = await fetch(`${API_BASE}/space/${spaceId}`, { headers: getHeaders() })
    return res.json()
  },

  async deleteSpace(spaceId) {
    const res = await fetch(`${API_BASE}/space/${spaceId}`, {
      method: 'DELETE',
      headers: getHeaders(),
    })
    return res.json()
  },

  // ─── AI Chat ───
  async sendMessage(spaceId, message) {
    const res = await fetch(`${AI_BASE}/chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ spaceId, message }),
    })
    return res.json()
  },

  async getChatHistory(spaceId) {
    const res = await fetch(`${AI_BASE}/history/${spaceId}`, { headers: getHeaders() })
    return res.json()
  },
}

/**
 * Connect to the WebSocket server.
 * WHY a separate function? WebSocket is a different protocol (ws://) from HTTP.
 * It maintains a persistent connection for real-time communication.
 */
export function connectWebSocket(spaceId, onMessage) {
  const token = getToken()
  // In dev, Vite proxy handles /ws -> ws://localhost:8001
  // In prod, Nginx handles the upgrade
  const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws`
  const ws = new WebSocket(wsUrl)

  ws.onopen = () => {
    // First message must be "join" with the space ID and auth token
    ws.send(JSON.stringify({
      type: 'join',
      payload: { spaceId, token },
    }))
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    onMessage(data)
  }

  ws.onerror = (err) => {
    console.error('WebSocket error:', err)
  }

  return ws
}
