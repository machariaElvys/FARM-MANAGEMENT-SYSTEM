import { useEffect, useState } from 'react'
import { readRecords } from '../offline/db.js'
import { summarizeRecords } from '../offline/report.js'
import { api, harvestSummary, money } from '../services/api.js'

export default function ReportsPage({ token, userId }) {
  const [report, setReport] = useState(null)
  const [year, setYear] = useState(new Date().getFullYear())
  const [error, setError] = useState('')

  useEffect(() => {
    async function load() {
      try {
        setReport(await api(`/reports/summary?year=${year}`, { token }))
        setError('')
      } catch (requestError) {
        const cached = await readRecords(userId)
        setReport(summarizeRecords(cached, year))
        setError(cached.length ? '' : requestError.message)
      }
    }
    load()
    window.addEventListener('farm:sync-complete', load)
    return () => window.removeEventListener('farm:sync-complete', load)
  }, [token, userId, year])

  return (
    <div className="page-stack">
      <section className="page-heading"><div><span className="eyebrow">YOUR FARM, SUMMARIZED</span><h1>Reports</h1><p>Review recorded activity, costs and sales by year.</p></div><label className="year-picker">Report year<select value={year} onChange={(event) => setYear(Number(event.target.value))}>{Array.from({ length: 7 }, (_, index) => new Date().getFullYear() - index).map((item) => <option key={item}>{item}</option>)}</select></label></section>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <section className="report-summary-grid">
        <ReportCard label="Total expenses" value={report ? money(report.expenses) : '—'} detail="Inputs, labour and other expenses" />
        <ReportCard label="Sales recorded" value={report ? money(report.sales) : '—'} detail="Sales entries for the selected year" />
        <ReportCard label="Harvest quantity" value={harvestSummary(report)} detail="Grouped by unit from harvest records" />
      </section>
      <section className="panel report-panel"><div className="panel-heading"><div><span className="eyebrow">ACTIVITY BREAKDOWN</span><h2>Entries by category</h2></div></div>
        {report?.categories?.length ? <div className="report-category-list">{report.categories.map((item) => <div className="report-category-row" key={item.name}><div className="report-category-icon">{item.label.charAt(0)}</div><div className="report-category-name"><strong>{item.label}</strong><span>{item.count} {item.count === 1 ? 'entry' : 'entries'}</span></div><div className="report-category-amount">{item.amount ? money(item.amount) : '—'}</div><div className="report-progress"><span style={{ width: `${Math.max(5, (item.count / report.record_count) * 100)}%` }} /></div></div>)}</div> : <div className="empty-state"><span className="empty-sun">✳</span><p>No records for {year} yet. Add entries to build your report.</p></div>}
      </section>
      <p className="report-footnote">Summaries are calculated from the entries currently in your ledger.</p>
    </div>
  )
}

function ReportCard({ label, value, detail }) {
  return <article className="report-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></article>
}
