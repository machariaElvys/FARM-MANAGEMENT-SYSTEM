import { useEffect, useState } from 'react'
import AuthPanel from './components/AuthPanel.jsx'
import AdminPage from './components/AdminPage.jsx'
import Dashboard from './components/Dashboard.jsx'
import RecordsPage from './components/RecordsPage.jsx'
import ReportsPage from './components/ReportsPage.jsx'
import Sidebar from './components/Sidebar.jsx'
import SyncStatus from './components/SyncStatus.jsx'
import { api } from './services/api.js'

const pageTitles = { dashboard: 'Overview', records: 'Farm records', reports: 'Reports', admin: 'Administration' }

export default function App() {
  const [session, setSession] = useState(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [view, setView] = useState('dashboard')

  useEffect(() => {
    const savedToken = localStorage.getItem('shamba.access-token')
    let cachedUser = null
    try { cachedUser = JSON.parse(localStorage.getItem('shamba.user') || 'null') } catch { cachedUser = null }
    if (!savedToken) {
      setCheckingSession(false)
      return
    }
    api('/auth/me', { token: savedToken })
      .then((user) => {
        localStorage.setItem('shamba.user', JSON.stringify(user))
        setSession({ access_token: savedToken, user })
      })
      .catch((error) => {
        if (error.status !== 401 && cachedUser) setSession({ access_token: savedToken, user: cachedUser })
        else {
          localStorage.removeItem('shamba.access-token')
          localStorage.removeItem('shamba.user')
        }
      })
      .finally(() => setCheckingSession(false))
  }, [])

  function signIn(nextSession) {
    localStorage.setItem('shamba.access-token', nextSession.access_token)
    localStorage.setItem('shamba.user', JSON.stringify(nextSession.user))
    setSession(nextSession)
    setView('dashboard')
  }

  function signOut() {
    localStorage.removeItem('shamba.access-token')
    localStorage.removeItem('shamba.user')
    setSession(null)
  }

  if (checkingSession) return <main className="loading-screen"><span className="brand-mark">S</span><p>Opening your farm workspace…</p></main>
  if (!session) return <AuthPanel onAuthenticated={signIn} />

  return (
    <div className="app-shell">
      <Sidebar active={view} onNavigate={setView} user={session.user} onSignOut={signOut} />
      <main className="main-area">
        <header className="topbar"><div className="breadcrumb">Farm workspace <span>/</span> <strong>{pageTitles[view]}</strong></div><div className="topbar-right"><SyncStatus token={session.access_token} userId={session.user.id} /><span className="season-chip"><span /> {new Date().getFullYear()} season</span><div className="top-avatar">{session.user.name.trim().charAt(0).toUpperCase()}</div></div></header>
        <div className="page-content">
          {view === 'dashboard' && <Dashboard token={session.access_token} user={session.user} onNavigate={setView} />}
          {view === 'records' && <RecordsPage token={session.access_token} userId={session.user.id} />}
          {view === 'reports' && <ReportsPage token={session.access_token} userId={session.user.id} />}
          {view === 'admin' && session.user.role === 'admin' && <AdminPage token={session.access_token} />}
        </div>
      </main>
    </div>
  )
}
