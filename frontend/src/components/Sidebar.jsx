const items = [
  { id: 'dashboard', label: 'Overview', icon: '◫' },
  { id: 'records', label: 'Farm records', icon: '▤' },
  { id: 'reports', label: 'Reports', icon: '▥' },
]

export default function Sidebar({ active, onNavigate, user, onSignOut }) {
  return (
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">S</span><span>Shamba Ledger</span></div>
      <div className="side-label">FARM WORKSPACE</div>
      <nav className="side-nav" aria-label="Main navigation">
        {items.map((item) => (
          <button key={item.id} className={`nav-item ${active === item.id ? 'selected' : ''}`} onClick={() => onNavigate(item.id)}>
            <span className="nav-icon" aria-hidden="true">{item.icon}</span>{item.label}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="help-card"><span className="help-icon">✳</span><strong>Your farm, at a glance</strong><p>A simple place for the details that help you plan the next season.</p></div>
        <div className="profile-row">
          <div className="avatar">{user.name.trim().charAt(0).toUpperCase()}</div>
          <div className="profile-copy"><strong>{user.name}</strong><span>Farmer account</span></div>
          <button className="signout" title="Sign out" aria-label="Sign out" onClick={onSignOut}>↗</button>
        </div>
      </div>
    </aside>
  )
}
