import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../hooks/useApi'

/**
 * Login/Signup page.
 *
 * Simple form with username/password. Toggle between login and signup.
 * On success, stores the JWT in localStorage and redirects to /spaces.
 *
 * WHY localStorage for tokens?
 * Simple and works for learning. In production, httpOnly cookies are more
 * secure (immune to XSS), but they add complexity (CSRF protection needed).
 * For a DevOps learning project, localStorage is fine.
 */
export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isSignup, setIsSignup] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    try {
      if (isSignup) {
        await api.signup(username, password, 'user')
        // After signup, auto-login
        await api.signin(username, password)
      } else {
        await api.signin(username, password)
      }
      navigate('/spaces')
    } catch (err) {
      setError(err.message || 'Something went wrong')
    }
  }

  return (
    <div className="container" style={{ marginTop: '10vh' }}>
      <h1>2D Metaverse by Prathmesh Kurhade</h1>
      <p style={{ color: '#999', marginBottom: '2rem' }}>
        {isSignup ? 'Create an account' : 'Sign in to continue'}
      </p>

      <form onSubmit={handleSubmit} style={{ maxWidth: 400 }}>
        <div className="form-group">
          <label>Username</label>
          <input
            value={username}
            onChange={e => setUsername(e.target.value)}
            placeholder="Enter username"
            required
          />
        </div>
        <div className="form-group">
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            placeholder="Enter password"
            required
          />
        </div>
        {error && <p className="error">{error}</p>}
        <button type="submit" style={{ width: '100%', marginTop: '0.5rem' }}>
          {isSignup ? 'Sign Up' : 'Sign In'}
        </button>
      </form>

      <p style={{ marginTop: '1rem', color: '#999' }}>
        {isSignup ? 'Already have an account?' : "Don't have an account?"}{' '}
        <span
          onClick={() => setIsSignup(!isSignup)}
          style={{ color: '#2563eb', cursor: 'pointer' }}
        >
          {isSignup ? 'Sign In' : 'Sign Up'}
        </span>
      </p>
    </div>
  )
}
