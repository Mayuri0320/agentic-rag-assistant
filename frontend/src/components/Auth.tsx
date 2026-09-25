import { useState } from 'react'
import type { FormEvent } from 'react'
import { login, register } from '../api/client'
import type { TokenResponse } from '../api/client'

type AuthMode = 'login' | 'register'

type AuthProps = {
  onAuthenticated: (tokens: TokenResponse) => void
}

function Auth({ onAuthenticated }: AuthProps) {
  const [mode, setMode] = useState<AuthMode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError('')
    setLoading(true)

    try {
      const tokens =
        mode === 'login'
          ? await login(email, password)
          : await register(email, password)

      onAuthenticated(tokens)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Something went wrong.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <div className="auth-brand">
          <div className="auth-brand-mark">?</div>

          <div>
            <h1>Agentic RAG</h1>
            <p>AI Assistant</p>
          </div>
        </div>

        <div className="auth-heading">
          <h2>{mode === 'login' ? 'Welcome back' : 'Create your account'}</h2>

          <p>
            {mode === 'login'
              ? 'Sign in to continue to your AI workspace.'
              : 'Create an account to start using Agentic RAG.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Minimum 8 characters"
              minLength={8}
              required
            />
          </label>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading
              ? 'Please wait...'
              : mode === 'login'
                ? 'Sign in'
                : 'Create account'}
          </button>
        </form>

        <div className="auth-switch">
          <span>
            {mode === 'login'
              ? "Don't have an account?"
              : 'Already have an account?'}
          </span>

          <button
            type="button"
            onClick={() => {
              setMode(mode === 'login' ? 'register' : 'login')
              setError('')
            }}
          >
            {mode === 'login' ? 'Create account' : 'Sign in'}
          </button>
        </div>
      </section>
    </main>
  )
}

export default Auth

