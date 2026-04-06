import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../hooks/useApi'
import { LogIn, UserPlus, Gamepad2 } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isSignup, setIsSignup] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isSignup) {
        await api.signup(username, password, 'user')
        await api.signin(username, password)
      } else {
        await api.signin(username, password)
      }
      // Go to avatar select if no avatar chosen yet, otherwise spaces
      const hasAvatar = localStorage.getItem('avatarId')
      navigate(hasAvatar ? '/spaces' : '/avatar')
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      {/* Animated grid background */}
      <div className="grid-bg" />

      <div className="login-container">
        {/* Logo / Title */}
        <div className="login-header">
          <div className="login-icon">
            <Gamepad2 size={40} />
          </div>
          <h1 className="login-title">METAVERSE</h1>
          <p className="login-subtitle">
            {isSignup ? 'Create your identity' : 'Enter the grid'}
          </p>
        </div>

        {/* Form Card */}
        <form onSubmit={handleSubmit} className="login-card">
          <div className="input-group">
            <label>Username</label>
            <input
              value={username}
              onChange={e => setUsername(e.target.value)}
              placeholder="Choose a name..."
              required
              autoComplete="off"
            />
          </div>

          <div className="input-group">
            <label>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="Secret code..."
              required
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {isSignup ? (
              <><UserPlus size={18} /> {loading ? 'Creating...' : 'Sign Up'}</>
            ) : (
              <><LogIn size={18} /> {loading ? 'Entering...' : 'Sign In'}</>
            )}
          </button>
        </form>

        {/* Toggle */}
        <p className="login-toggle">
          {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
          <span onClick={() => { setIsSignup(!isSignup); setError('') }}>
            {isSignup ? 'Sign In' : 'Sign Up'}
          </span>
        </p>
      </div>
    </div>
  )
}
