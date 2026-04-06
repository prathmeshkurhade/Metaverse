import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../hooks/useApi'
import { Plus, Trash2, DoorOpen, LogOut, Map, Grid3X3, Globe, Lock, Users } from 'lucide-react'

export default function Spaces() {
  const [mySpaces, setMySpaces] = useState([])
  const [publicSpaces, setPublicSpaces] = useState([])
  const [tab, setTab] = useState('mine') // 'mine' or 'public'
  const [name, setName] = useState('')
  const [dimensions, setDimensions] = useState('50x50')
  const [isPublic, setIsPublic] = useState(false)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login')
      return
    }
    loadAll()
  }, [])

  async function loadAll() {
    try {
      const [mine, pub] = await Promise.all([
        api.listSpaces(),
        api.listPublicSpaces(),
      ])
      setMySpaces(mine.spaces || [])
      setPublicSpaces(pub.spaces || [])
    } catch {
      navigate('/login')
    } finally {
      setLoading(false)
    }
  }

  async function handleCreate(e) {
    e.preventDefault()
    if (!name || !dimensions) return
    setCreating(true)
    try {
      await api.createSpace(name, dimensions, isPublic)
      setName('')
      setIsPublic(false)
      loadAll()
    } finally {
      setCreating(false)
    }
  }

  async function handleDelete(spaceId) {
    await api.deleteSpace(spaceId)
    loadAll()
  }

  const spaces = tab === 'mine' ? mySpaces : publicSpaces

  if (loading) {
    return (
      <div className="spaces-page">
        <div className="grid-bg" />
        <div className="spaces-container">
          <p style={{ color: '#666', textAlign: 'center', marginTop: '4rem' }}>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="spaces-page">
      <div className="grid-bg" />

      <div className="spaces-container">
        {/* Header */}
        <div className="spaces-header">
          <div>
            <h1 className="spaces-title">
              <Map size={28} /> Metaverse
            </h1>
            <p className="spaces-subtitle">{mySpaces.length} world{mySpaces.length !== 1 ? 's' : ''} created</p>
          </div>
          <button
            className="btn-ghost"
            onClick={() => { localStorage.removeItem('token'); localStorage.removeItem('avatarId'); navigate('/login') }}
          >
            <LogOut size={18} /> Logout
          </button>
        </div>

        {/* Create Space Form */}
        <form onSubmit={handleCreate} className="create-form">
          <div className="create-form-inputs">
            <div className="input-group" style={{ flex: 1 }}>
              <label>World Name</label>
              <input
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="Name your world..."
                required
              />
            </div>
            <div className="input-group" style={{ width: 130 }}>
              <label>Size</label>
              <input
                value={dimensions}
                onChange={e => setDimensions(e.target.value)}
                placeholder="50x50"
              />
            </div>
            <div
              className={`visibility-toggle ${isPublic ? 'is-public' : ''}`}
              onClick={() => setIsPublic(!isPublic)}
              title={isPublic ? 'Public -- anyone can join' : 'Private -- only you'}
            >
              {isPublic ? <Globe size={18} /> : <Lock size={18} />}
              <span>{isPublic ? 'Public' : 'Private'}</span>
            </div>
            <button type="submit" className="btn-primary create-btn" disabled={creating}>
              <Plus size={18} /> {creating ? '...' : 'Create'}
            </button>
          </div>
        </form>

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${tab === 'mine' ? 'tab-active' : ''}`}
            onClick={() => setTab('mine')}
          >
            <Lock size={15} /> My Worlds ({mySpaces.length})
          </button>
          <button
            className={`tab ${tab === 'public' ? 'tab-active' : ''}`}
            onClick={() => setTab('public')}
          >
            <Globe size={15} /> Public Worlds ({publicSpaces.length})
          </button>
        </div>

        {/* Space Grid */}
        {spaces.length === 0 ? (
          <div className="empty-state">
            <Grid3X3 size={48} strokeWidth={1} />
            <p>{tab === 'mine' ? 'No worlds yet' : 'No public worlds yet'}</p>
            <span>{tab === 'mine' ? 'Create your first world above' : 'Be the first to create a public world!'}</span>
          </div>
        ) : (
          <div className="spaces-grid">
            {spaces.map(space => {
              const [w, h] = (space.dimensions || '0x0').split('x')
              const isMine = tab === 'mine'
              return (
                <div key={space.id} className="space-card">
                  <div className="space-card-preview">
                    <div className="mini-grid" />
                    <span className="space-card-size">{w}×{h}</span>
                    {space.isPublic && (
                      <span className="space-card-badge"><Globe size={10} /> Public</span>
                    )}
                  </div>

                  <div className="space-card-body">
                    <h3>{space.name}</h3>
                    {!isMine && space.creatorName && (
                      <p className="space-card-creator">
                        <Users size={12} /> by {space.creatorName}
                      </p>
                    )}
                    <div className="space-card-actions">
                      <button className="btn-primary" onClick={() => navigate(`/arena/${space.id}`)}>
                        <DoorOpen size={16} /> {isMine ? 'Enter' : 'Join'}
                      </button>
                      {isMine && (
                        <button className="btn-danger" onClick={() => handleDelete(space.id)}>
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
