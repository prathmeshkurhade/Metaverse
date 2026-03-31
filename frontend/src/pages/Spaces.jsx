import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../hooks/useApi'

/**
 * Spaces page -- list, create, and delete rooms.
 *
 * This is the "lobby" of the metaverse. Users see their rooms and can
 * create new ones or join existing ones.
 */
export default function Spaces() {
  const [spaces, setSpaces] = useState([])
  const [name, setName] = useState('')
  const [dimensions, setDimensions] = useState('100x100')
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  // Check auth on mount
  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }
    loadSpaces()
  }, [])

  async function loadSpaces() {
    try {
      const data = await api.listSpaces()
      setSpaces(data.spaces || [])
    } catch {
      // Token expired or invalid
      navigate('/login')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!name || !dimensions) return
    await api.createSpace(name, dimensions)
    setName('')
    loadSpaces()
  }

  async function handleDelete(spaceId) {
    await api.deleteSpace(spaceId)
    loadSpaces()
  }

  if (loading) return <div className="container"><p>Loading...</p></div>

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Your Spaces</h1>
        <button onClick={() => { localStorage.removeItem('token'); navigate('/login') }}>
          Logout
        </button>
      </div>

      {/* Create Space Form */}
      <form onSubmit={handleCreate} className="card" style={{ display: 'flex', gap: '0.5rem', alignItems: 'end' }}>
        <div className="form-group" style={{ flex: 1, marginBottom: 0 }}>
          <label>Name</label>
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Room name" />
        </div>
        <div className="form-group" style={{ width: 120, marginBottom: 0 }}>
          <label>Size</label>
          <input value={dimensions} onChange={e => setDimensions(e.target.value)} placeholder="100x100" />
        </div>
        <button type="submit">Create</button>
      </form>

      {/* Space List */}
      {spaces.length === 0 ? (
        <p style={{ color: '#666', marginTop: '2rem' }}>No spaces yet. Create one above!</p>
      ) : (
        <div className="space-grid">
          {spaces.map(space => (
            <div key={space.id} className="card">
              <h3>{space.name}</h3>
              <p style={{ color: '#999', fontSize: '0.875rem' }}>
                {space.dimensions}
              </p>
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.75rem' }}>
                <button onClick={() => navigate(`/arena/${space.id}`)}>
                  Enter
                </button>
                <button
                  onClick={() => handleDelete(space.id)}
                  style={{ background: '#dc2626', borderColor: '#dc2626' }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
