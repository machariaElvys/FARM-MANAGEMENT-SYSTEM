import { useState } from 'react'
import { api } from '../services/api.js'

export default function AuthPanel({ onAuthenticated }) {
  const [mode, setMode] = useState('login')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const registering = mode === 'register'

  async function submit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const session = await api(registering ? '/auth/register' : '/auth/login', {
        method: 'POST',
        body: registering ? { name, email, password } : { email, password },
      })
      onAuthenticated(session)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <div className="brand brand-light"><span className="brand-mark">S</span><span>Shamba Ledger</span></div>
        <div className="auth-story-copy">
          <span className="eyebrow eyebrow-light">A clearer picture of your farm</span>
          <h1>Good records make room for better decisions.</h1>
          <p>Keep planting, input, labour, harvest and sales information together, season after season.</p>
        </div>
        <div className="story-note"><span className="story-dot" /> Built for the everyday work of small farms</div>
      </section>
      <section className="auth-form-side">
        <form className="auth-card" onSubmit={submit}>
          <span className="eyebrow">WELCOME TO SHAMBA LEDGER</span>
          <h2>{registering ? 'Create your account' : 'Welcome back'}</h2>
          <p className="muted">{registering ? 'Start keeping your farm records in one place.' : 'Sign in to see what is happening on your farm.'}</p>
          {registering && (
            <label className="field">Your name
              <input autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} required minLength="2" maxLength="120" placeholder="e.g. Wanjiku Kamau" />
            </label>
          )}
          <label className="field">Email address
            <input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} required placeholder="you@example.com" />
          </label>
          <label className="field">Password
            <input type="password" autoComplete={registering ? 'new-password' : 'current-password'} value={password} onChange={(event) => setPassword(event.target.value)} required minLength={registering ? 8 : undefined} placeholder={registering ? 'At least 8 characters' : 'Enter your password'} />
          </label>
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary auth-submit" disabled={busy} type="submit">{busy ? 'Please wait…' : registering ? 'Create account' : 'Sign in'} <span aria-hidden="true">→</span></button>
          <p className="auth-switch">{registering ? 'Already have an account?' : 'New to Shamba Ledger?'}{' '}
            <button type="button" className="text-button" onClick={() => { setMode(registering ? 'login' : 'register'); setError('') }}>{registering ? 'Sign in' : 'Create an account'}</button>
          </p>
        </form>
        <p className="auth-footnote">Your farm information is private to your account.</p>
      </section>
    </main>
  )
}
