import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, connectWebSocket } from '../hooks/useApi'

/**
 * Arena page -- the actual 2D metaverse room.
 *
 * Three main features:
 * 1. Canvas: renders a grid with elements and user avatars
 * 2. WebSocket: real-time position updates
 * 3. Chat sidebar: AI Room Assistant
 *
 * WHY Canvas (not DOM elements)?
 * A space can have 100+ elements and 20+ users. Rendering each as a DOM
 * element would be slow (DOM operations are expensive). Canvas draws pixels
 * directly to a bitmap -- much faster for game-like rendering.
 */

const TILE_SIZE = 20  // Each grid unit = 20x20 pixels on screen
const AVATAR_COLORS = ['#ef4444', '#3b82f6', '#22c55e', '#f59e0b', '#8b5cf6', '#ec4899']

export default function Arena() {
  const { spaceId } = useParams()
  const navigate = useNavigate()
  const canvasRef = useRef(null)
  const wsRef = useRef(null)

  // State
  const [myPosition, setMyPosition] = useState(null)
  const [users, setUsers] = useState({})  // userId -> {x, y}
  const [elements, setElements] = useState([])
  const [dimensions, setDimensions] = useState({ w: 100, h: 100 })
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [myUserId, setMyUserId] = useState(null)

  // Load space details and connect WebSocket
  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }

    // Fetch space elements for rendering
    api.getSpace(spaceId).then(data => {
      if (data.dimensions) {
        const [w, h] = data.dimensions.split('x').map(Number)
        setDimensions({ w, h })
      }
      setElements(data.elements || [])
    })

    // Load existing chat history
    api.getChatHistory(spaceId).then(data => {
      setMessages(data.messages || [])
    }).catch(() => {})

    // Connect WebSocket
    const ws = connectWebSocket(spaceId, handleWsMessage)
    wsRef.current = ws

    return () => {
      if (ws.readyState === WebSocket.OPEN) ws.close()
    }
  }, [spaceId])

  // Handle keyboard movement
  useEffect(() => {
    function handleKeyDown(e) {
      if (!myPosition || !wsRef.current) return

      let newX = myPosition.x
      let newY = myPosition.y

      switch (e.key) {
        case 'ArrowUp':    case 'w': newY -= 1; break
        case 'ArrowDown':  case 's': newY += 1; break
        case 'ArrowLeft':  case 'a': newX -= 1; break
        case 'ArrowRight': case 'd': newX += 1; break
        default: return
      }

      e.preventDefault()

      // Optimistic update -- move immediately, server will correct if invalid
      setMyPosition({ x: newX, y: newY })

      wsRef.current.send(JSON.stringify({
        type: 'move',
        payload: { x: newX, y: newY },
      }))
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [myPosition])

  // Redraw canvas whenever state changes
  useEffect(() => {
    draw()
  }, [myPosition, users, elements, dimensions])

  function handleWsMessage(data) {
    switch (data.type) {
      case 'space-joined':
        setMyPosition(data.payload.spawn)
        // Store existing users
        const userMap = {}
        data.payload.users.forEach(u => { userMap[u.userId] = { x: u.x, y: u.y } })
        setUsers(userMap)
        break

      case 'user-joined':
        setUsers(prev => ({
          ...prev,
          [data.payload.userId]: { x: data.payload.x, y: data.payload.y },
        }))
        break

      case 'movement':
        setUsers(prev => ({
          ...prev,
          [data.payload.userId]: { x: data.payload.x, y: data.payload.y },
        }))
        break

      case 'movement-rejected':
        // Server corrected our position
        setMyPosition({ x: data.payload.x, y: data.payload.y })
        break

      case 'user-left':
        setUsers(prev => {
          const next = { ...prev }
          delete next[data.payload.userId]
          return next
        })
        break
    }
  }

  function draw() {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    const canvasW = dimensions.w * TILE_SIZE
    const canvasH = dimensions.h * TILE_SIZE
    canvas.width = Math.min(canvasW, 800)
    canvas.height = Math.min(canvasH, 600)

    // Viewport offset (center on player)
    let offsetX = 0, offsetY = 0
    if (myPosition) {
      offsetX = Math.max(0, myPosition.x * TILE_SIZE - canvas.width / 2)
      offsetY = Math.max(0, myPosition.y * TILE_SIZE - canvas.height / 2)
    }

    // Clear
    ctx.fillStyle = '#111'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Draw grid lines
    ctx.strokeStyle = '#222'
    ctx.lineWidth = 0.5
    for (let x = 0; x < canvasW; x += TILE_SIZE) {
      const screenX = x - offsetX
      if (screenX >= 0 && screenX <= canvas.width) {
        ctx.beginPath()
        ctx.moveTo(screenX, 0)
        ctx.lineTo(screenX, canvas.height)
        ctx.stroke()
      }
    }
    for (let y = 0; y < canvasH; y += TILE_SIZE) {
      const screenY = y - offsetY
      if (screenY >= 0 && screenY <= canvas.height) {
        ctx.beginPath()
        ctx.moveTo(0, screenY)
        ctx.lineTo(canvas.width, screenY)
        ctx.stroke()
      }
    }

    // Draw elements (green squares)
    ctx.fillStyle = '#166534'
    elements.forEach(el => {
      const sx = el.x * TILE_SIZE - offsetX
      const sy = el.y * TILE_SIZE - offsetY
      ctx.fillRect(sx + 2, sy + 2, TILE_SIZE - 4, TILE_SIZE - 4)
    })

    // Draw other users
    Object.entries(users).forEach(([userId, pos], idx) => {
      const sx = pos.x * TILE_SIZE - offsetX
      const sy = pos.y * TILE_SIZE - offsetY
      ctx.fillStyle = AVATAR_COLORS[idx % AVATAR_COLORS.length]
      ctx.beginPath()
      ctx.arc(sx + TILE_SIZE / 2, sy + TILE_SIZE / 2, TILE_SIZE / 2 - 2, 0, Math.PI * 2)
      ctx.fill()
    })

    // Draw my avatar (white circle)
    if (myPosition) {
      const sx = myPosition.x * TILE_SIZE - offsetX
      const sy = myPosition.y * TILE_SIZE - offsetY
      ctx.fillStyle = '#fff'
      ctx.beginPath()
      ctx.arc(sx + TILE_SIZE / 2, sy + TILE_SIZE / 2, TILE_SIZE / 2 - 2, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  async function handleSendMessage(e) {
    e.preventDefault()
    if (!chatInput.trim()) return

    const msg = chatInput.trim()
    setChatInput('')

    // Optimistic: add user message immediately
    setMessages(prev => [...prev, { role: 'user', content: msg }])

    try {
      const data = await api.sendMessage(spaceId, msg)
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }])
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Error: AI service unavailable' }])
    }
  }

  return (
    <div className="arena-container">
      {/* Canvas */}
      <div className="canvas-wrapper">
        <canvas ref={canvasRef} />
        <div style={{ position: 'absolute', top: 8, left: 8, color: '#666', fontSize: '0.75rem' }}>
          {myPosition ? `Position: (${myPosition.x}, ${myPosition.y})` : 'Connecting...'} |
          {' '}{Object.keys(users).length} other user(s) |
          {' '}WASD or Arrow keys to move
        </div>
        <button
          onClick={() => navigate('/spaces')}
          style={{ position: 'absolute', top: 8, right: 8, fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
        >
          Leave
        </button>
      </div>

      {/* Chat Sidebar */}
      <div className="chat-sidebar">
        <div style={{ padding: '0.75rem', borderBottom: '1px solid #333', fontWeight: 600 }}>
          AI Room Assistant
        </div>
        <div className="chat-messages">
          {messages.length === 0 && (
            <p style={{ color: '#666', fontSize: '0.875rem' }}>
              Ask me anything about this room!
            </p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <div style={{ fontSize: '0.7rem', color: '#999', marginBottom: '0.25rem' }}>
                {msg.role === 'user' ? 'You' : 'AI'}
              </div>
              {msg.content}
            </div>
          ))}
        </div>
        <form onSubmit={handleSendMessage} className="chat-input">
          <input
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            placeholder="Ask the AI..."
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  )
}
