import { useEffect, useState } from 'react'
import AuthPanel from './components/AuthPanel.jsx'
import Dashboard from './components/Dashboard.jsx'
import RecordsPage from './components/RecordsPage.jsx'
import ReportsPage from './components/ReportsPage.jsx'
import Sidebar from './components/Sidebar.jsx'
import { api } from './services/api.js'

const pageTitles = { dashboard: 'Overview', records: 'Farm records', reports: 'Reports' }

export default function App() {
  const [session, setSession] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [view, setView] = useState('dashboard')

  useEffect(() => {
    const savedToken = localStorage.getItem('shamba.access-token')
    if (!savedToken) {
      setCheckingSession(false)
      return
    }
    api('/auth/me', { token: savedToken })
      .then((user) => setSession({ access_token: savedToken, user }))
      .catch(() => localStorage.removeItem('shamba.access-token'))
      .finally(() => setCheckingSession(false))
  }, [])

  function signIn(nextSession) {
    localStorage.setItem('shamba.access-token', nextSession.access_token)
    setSession(nextSession)
    setView('dashboard')
  }

  function signOut() {
    localStorage.removeItem('shamba.access-token')
    setSession(null)
  }

  if (checkingSession) return <main className="loading-screen"><span className="brand-mark">S</span><p>Opening your farm workspace…</p></main>
  if (!session) return <AuthPanel onAuthenticated={signIn} />

  return (
    <div className="app-shell">
      <Sidebar active={view} onNavigate={setView} user={session.user} onSignOut={signOut} />
      <main className="main-area">
        <header className="topbar"><div className="breadcrumb">Farm workspace <span>/</span> <strong>{pageTitles[view]}</strong></div><div className="topbar-right"><span className="season-chip"><span /> {new Date().getFullYear()} season</span><div className="top-avatar">{session.user.name.trim().charAt(0).toUpperCase()}</div></div></header>
        <div className="page-content">
          {view === 'dashboard' && <Dashboard token={session.access_token} user={session.user} onNavigate={setView} />}
          {view === 'records' && <RecordsPage token={session.access_token} />}
          {view === 'reports' && <ReportsPage token={session.access_token} />}
        </div>
      </main>
    </div>
  )
}
