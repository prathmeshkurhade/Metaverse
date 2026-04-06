import { useEffect, useRef, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api, connectWebSocket } from '../hooks/useApi'
import { ArrowLeft, Bot, Send } from 'lucide-react'
import { AVATARS, drawSprite } from '../sprites'

const TILE_SIZE = 24

export default function Arena() {
  const { spaceId } = useParams()
  const navigate = useNavigate()
  const canvasRef = useRef(null)
  const wsRef = useRef(null)

  const [myPosition, setMyPosition] = useState(null)
  const [users, setUsers] = useState({})
  const [elements, setElements] = useState([])
  const [dimensions, setDimensions] = useState({ w: 100, h: 100 })
  const [messages, setMessages] = useState([])
  const [chatInput, setChatInput] = useState('')

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }

    api.getSpace(spaceId).then(data => {
      if (data.dimensions) {
        const [w, h] = data.dimensions.split('x').map(Number)
        setDimensions({ w, h })
      }
      setElements(data.elements || [])
    })

    api.getChatHistory(spaceId).then(data => {
      setMessages(data.messages || [])
    }).catch(() => {})

    const ws = connectWebSocket(spaceId, handleWsMessage)
    wsRef.current = ws

    return () => {
      if (ws.readyState === WebSocket.OPEN) ws.close()
    }
  }, [spaceId])

  useEffect(() => {
    function handleKeyDown(e) {
      if (!myPosition || !wsRef.current) return
      // Don't capture keys when typing in chat
      if (e.target.tagName === 'INPUT') return

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

      // Client-side collision check (prevents jitter from server rejection)
      const blocked = elements.some(el => el.x === newX && el.y === newY)
      if (blocked) return

      setMyPosition({ x: newX, y: newY })
      wsRef.current.send(JSON.stringify({
        type: 'move',
        payload: { x: newX, y: newY },
      }))
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [myPosition])

  useEffect(() => {
    draw()
  }, [myPosition, users, elements, dimensions])

  function handleWsMessage(data) {
    switch (data.type) {
      case 'space-joined':
        setMyPosition(data.payload.spawn)
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
    canvas.width = Math.min(canvasW, window.innerWidth - 320)
    canvas.height = window.innerHeight

    let offsetX = 0, offsetY = 0
    if (myPosition) {
      offsetX = Math.max(0, myPosition.x * TILE_SIZE - canvas.width / 2)
      offsetY = Math.max(0, myPosition.y * TILE_SIZE - canvas.height / 2)
    }

    // Background
    ctx.fillStyle = '#0a0a0f'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // Grid lines
    ctx.strokeStyle = 'rgba(99, 102, 241, 0.06)'
    ctx.lineWidth = 1
    for (let x = 0; x < canvasW; x += TILE_SIZE) {
      const screenX = x - offsetX
      if (screenX >= -1 && screenX <= canvas.width + 1) {
        ctx.beginPath()
        ctx.moveTo(screenX, 0)
        ctx.lineTo(screenX, canvas.height)
        ctx.stroke()
      }
    }
    for (let y = 0; y < canvasH; y += TILE_SIZE) {
      const screenY = y - offsetY
      if (screenY >= -1 && screenY <= canvas.height + 1) {
        ctx.beginPath()
        ctx.moveTo(0, screenY)
        ctx.lineTo(canvas.width, screenY)
        ctx.stroke()
      }
    }

    // Elements (obstacles) -- draw as trees/rocks based on position
    elements.forEach(el => {
      const sx = el.x * TILE_SIZE - offsetX
      const sy = el.y * TILE_SIZE - offsetY
      const t = TILE_SIZE

      // Alternate between tree and rock based on position for variety
      const isTree = (el.x + el.y) % 3 !== 0

      if (isTree) {
        // Tree: brown trunk + green foliage
        // Trunk
        ctx.fillStyle = '#78350f'
        ctx.fillRect(sx + t * 0.35, sy + t * 0.55, t * 0.3, t * 0.45)
        // Foliage (circle)
        ctx.fillStyle = '#166534'
        ctx.beginPath()
        ctx.arc(sx + t / 2, sy + t * 0.35, t * 0.4, 0, Math.PI * 2)
        ctx.fill()
        // Lighter highlight
        ctx.fillStyle = '#22c55e'
        ctx.beginPath()
        ctx.arc(sx + t * 0.4, sy + t * 0.28, t * 0.15, 0, Math.PI * 2)
        ctx.fill()
      } else {
        // Rock: gray with darker shadow
        ctx.fillStyle = '#374151'
        ctx.beginPath()
        ctx.moveTo(sx + t * 0.15, sy + t * 0.85)
        ctx.lineTo(sx + t * 0.3, sy + t * 0.2)
        ctx.lineTo(sx + t * 0.7, sy + t * 0.15)
        ctx.lineTo(sx + t * 0.9, sy + t * 0.55)
        ctx.lineTo(sx + t * 0.75, sy + t * 0.85)
        ctx.closePath()
        ctx.fill()
        // Highlight
        ctx.fillStyle = '#4b5563'
        ctx.beginPath()
        ctx.moveTo(sx + t * 0.3, sy + t * 0.25)
        ctx.lineTo(sx + t * 0.5, sy + t * 0.2)
        ctx.lineTo(sx + t * 0.6, sy + t * 0.4)
        ctx.lineTo(sx + t * 0.35, sy + t * 0.45)
        ctx.closePath()
        ctx.fill()
      }
    })

    // Other users -- draw pixel art sprites
    Object.entries(users).forEach(([, pos], idx) => {
      const sx = pos.x * TILE_SIZE - offsetX
      const sy = pos.y * TILE_SIZE - offsetY
      const sprite = AVATARS[idx % AVATARS.length]
      drawSprite(ctx, sprite, sx, sy, TILE_SIZE)
    })

    // My avatar -- draw my selected sprite with glow
    if (myPosition) {
      const sx = myPosition.x * TILE_SIZE - offsetX
      const sy = myPosition.y * TILE_SIZE - offsetY

      const myAvatarId = localStorage.getItem('avatarId') || 'knight'
      const mySprite = AVATARS.find(a => a.id === myAvatarId) || AVATARS[0]

      // Glow effect behind sprite
      ctx.shadowColor = mySprite.color
      ctx.shadowBlur = 12
      ctx.fillStyle = 'rgba(0,0,0,0)'
      ctx.fillRect(sx, sy, TILE_SIZE, TILE_SIZE)
      ctx.shadowBlur = 0

      drawSprite(ctx, mySprite, sx, sy, TILE_SIZE)
    }
  }

  async function handleSendMessage(e) {
    e.preventDefault()
    if (!chatInput.trim()) return

    const msg = chatInput.trim()
    setChatInput('')
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

        <div className="arena-hud">
          {myPosition && (
            <span className="hud-badge">
              {myPosition.x}, {myPosition.y}
            </span>
          )}
          <span className="hud-badge">
            {Object.keys(users).length} online
          </span>
          <span className="hud-badge">
            WASD to move
          </span>
        </div>

        <div className="arena-leave-btn">
          <button className="btn-ghost" onClick={() => navigate('/spaces')}>
            <ArrowLeft size={16} /> Leave
          </button>
        </div>
      </div>

      {/* Chat Sidebar */}
      <div className="chat-sidebar">
        <div className="chat-header">
          <Bot size={18} /> AI Assistant
        </div>
        <div className="chat-messages">
          {messages.length === 0 && (
            <p className="chat-empty">Ask me anything about this room</p>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`chat-message ${msg.role}`}>
              <div className="chat-message-role">
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
          <button type="submit"><Send size={16} /></button>
        </form>
      </div>
    </div>
  )
}
