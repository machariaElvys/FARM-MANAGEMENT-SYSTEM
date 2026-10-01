import { useEffect, useState } from 'react'
import { api, harvestSummary, money, shortDate } from '../services/api.js'

export default function Dashboard({ token, user, onNavigate }) {
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api('/reports/summary', { token }).then(setReport).catch((requestError) => setError(requestError.message))
  }, [token])

  const firstName = user.name.trim().split(/\s+/)[0]
  return (
    <div className="page-stack">
      <section className="welcome-banner">
        <div><span className="eyebrow eyebrow-light">YOUR FARM AT A GLANCE · {new Date().getFullYear()}</span><h1>Good morning, {firstName}.</h1><p>Here’s a snapshot of your farm records for this year.</p></div>
        <button className="button button-light" onClick={() => onNavigate('records')}>＋ Add a record</button>
        <span className="banner-orbit orbit-one" /><span className="banner-orbit orbit-two" />
      </section>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <section className="metric-grid" aria-label="Yearly farm summary">
        <Metric label="Farm expenses" value={report ? money(report.expenses) : '—'} icon="↗" tone="terra" note="Inputs, labour and other costs" />
        <Metric label="Sales recorded" value={report ? money(report.sales) : '—'} icon="↙" tone="green" note="From sales entries this year" />
        <Metric label="Harvest recorded" value={harvestSummary(report)} icon="✳" tone="gold" note="Quantity grouped by unit" />
        <Metric label="Farm entries" value={report ? report.record_count : '—'} icon="▤" tone="blue" note="All categories, this year" />
      </section>
      <section className="content-grid">
        <div className="panel recent-panel">
          <div className="panel-heading"><div><span className="eyebrow">THE LATEST</span><h2>Recent activity</h2></div><button className="text-button" onClick={() => onNavigate('records')}>View all <span aria-hidden="true">→</span></button></div>
          {report?.recent_records?.length ? <div className="activity-list">
            {report.recent_records.map((record) => <div className="activity-row" key={record.id}><span className="activity-mark">{record.category?.charAt(0) || '•'}</span><div className="activity-main"><strong>{record.title}</strong><span>{record.category} · {shortDate(record.occurred_on)}</span></div><div className="activity-value">{record.amount == null ? '—' : money(record.amount)}</div></div>)}
          </div> : <EmptyState message="Your farm activity will appear here once you add your first record." />}
        </div>
        <div className="panel category-panel">
          <div className="panel-heading"><div><span className="eyebrow">RECORD MIX</span><h2>By category</h2></div></div>
          {report?.categories?.length ? <div className="category-list">{report.categories.map((item) => <div className="category-row" key={item.name}><div className="category-row-top"><span>{item.label}</span><strong>{item.count}</strong></div><div className="category-track"><span style={{ width: `${Math.max(8, (item.count / report.record_count) * 100)}%` }} /></div></div>)}</div> : <EmptyState message="Categories will fill in as you record farm activities." />}
        </div>
      </section>
    </div>
  )
}

function Metric({ label, value, icon, tone, note }) {
  return <article className="metric-card"><div className="metric-top"><span>{label}</span><span className={`metric-icon ${tone}`}>{icon}</span></div><strong className="metric-value">{value}</strong><span className="metric-note">{note}</span></article>
}

function EmptyState({ message }) {
  return <div className="empty-state"><span className="empty-sun">✳</span><p>{message}</p></div>
}
