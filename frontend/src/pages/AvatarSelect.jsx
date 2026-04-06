import { useEffect, useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { AVATARS, drawSprite } from '../sprites'
import { Check } from 'lucide-react'

/**
 * Avatar selection screen.
 * Shown after login. User picks a pixel art character.
 * Selection is stored in localStorage (and could be synced to backend).
 */
export default function AvatarSelect() {
  const [selected, setSelected] = useState(null)
  const navigate = useNavigate()
  const canvasRefs = useRef({})

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }

    // Check if already has avatar
    const existing = localStorage.getItem('avatarId')
    if (existing) {
      setSelected(existing)
    }
  }, [])

  // Draw each sprite on its preview canvas
  useEffect(() => {
    AVATARS.forEach(avatar => {
      const canvas = canvasRefs.current[avatar.id]
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      ctx.clearRect(0, 0, 80, 80)
      drawSprite(ctx, avatar, 0, 0, 80)
    })
  }, [])

  function handleConfirm() {
    if (!selected) return
    localStorage.setItem('avatarId', selected)
    navigate('/spaces')
  }

  return (
    <div className="login-page">
      <div className="grid-bg" />

      <div style={{ position: 'relative', zIndex: 1, width: '100%', maxWidth: 600, padding: '2rem' }}>
        <div className="login-header">
          <h1 className="login-title">CHOOSE YOUR AVATAR</h1>
          <p className="login-subtitle">Pick your character for the metaverse</p>
        </div>

        <div className="avatar-grid">
          {AVATARS.map(avatar => (
            <div
              key={avatar.id}
              className={`avatar-card ${selected === avatar.id ? 'avatar-selected' : ''}`}
              onClick={() => setSelected(avatar.id)}
              style={{ '--avatar-color': avatar.color }}
            >
              <canvas
                ref={el => canvasRefs.current[avatar.id] = el}
                width={80}
                height={80}
                style={{ imageRendering: 'pixelated' }}
              />
              <span className="avatar-name">{avatar.name}</span>
              {selected === avatar.id && (
                <div className="avatar-check">
                  <Check size={16} />
                </div>
              )}
            </div>
          ))}
        </div>

        <button
          className="login-btn"
          style={{ width: '100%', marginTop: '1.5rem' }}
          onClick={handleConfirm}
          disabled={!selected}
        >
          {selected ? 'Enter Metaverse' : 'Select an avatar'}
        </button>
      </div>
    </div>
  )
}
