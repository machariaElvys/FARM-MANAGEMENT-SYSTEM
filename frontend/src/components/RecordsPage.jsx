import { useEffect, useMemo, useState } from 'react'
import RecordForm from './RecordForm.jsx'
import { api, money, shortDate } from '../services/api.js'

export default function RecordsPage({ token }) {
  const [records, setRecords] = useState([])
  const [query, setQuery] = useState('')
  const [editor, setEditor] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  async function loadRecords() {
    setLoading(true)
    try {
      setRecords(await api('/records?limit=500', { token }))
      setError('')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadRecords() }, [token])

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase()
    if (!normalized) return records
    return records.filter((record) => `${record.title} ${record.notes} ${record.category_label}`.toLowerCase().includes(normalized))
  }, [records, query])

  async function saveRecord(payload) {
    setSaving(true)
    setError('')
    try {
      const editing = editor?.id
      await api(editing ? `/records/${editing}` : '/records', { token, method: editing ? 'PUT' : 'POST', body: payload })
      setEditor(null)
      await loadRecords()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  async function removeRecord(record) {
    if (!window.confirm(`Delete “${record.title}”? This cannot be undone.`)) return
    try {
      await api(`/records/${record.id}`, { token, method: 'DELETE' })
      await loadRecords()
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  return (
    <div className="page-stack">
      <section className="page-heading"><div><span className="eyebrow">YOUR FARM LEDGER</span><h1>Farm records</h1><p>Keep day-to-day activities and costs easy to find.</p></div><button className="button button-primary" onClick={() => setEditor({})}>＋ Add a record</button></section>
      {error && <p className="inline-error" role="alert">{error}</p>}
      {editor !== null && <section className="panel editor-panel"><div className="panel-heading"><div><span className="eyebrow">FARM ACTIVITY</span><h2>{editor.id ? 'Edit record' : 'Add a record'}</h2></div><button className="icon-button" aria-label="Close form" onClick={() => setEditor(null)}>×</button></div><RecordForm initial={editor.id ? editor : null} onSubmit={saveRecord} onCancel={() => setEditor(null)} saving={saving} /></section>}
      <section className="panel table-panel">
        <div className="table-toolbar"><div className="record-count"><strong>{records.length}</strong> {records.length === 1 ? 'entry' : 'entries'} <span>in your ledger</span></div><label className="search-box"><span aria-hidden="true">⌕</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search your records" aria-label="Search farm records" /></label></div>
        {loading ? <div className="table-message">Loading your farm records…</div> : filtered.length ? <div className="table-scroll"><table><thead><tr><th>Activity</th><th>Type</th><th>Date</th><th>Quantity</th><th>Amount</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>{filtered.map((record) => <tr key={record.id}><td><div className="table-title">{record.title}</div>{record.notes && <div className="table-subtitle">{record.notes}</div>}</td><td><span className={`tag tag-${record.category}`}>{record.category_label}</span></td><td>{shortDate(record.occurred_on)}</td><td>{record.quantity == null ? '—' : `${Number(record.quantity).toLocaleString()} ${record.unit}`}</td><td className="amount-cell">{record.amount == null ? '—' : money(record.amount)}</td><td><div className="row-actions"><button onClick={() => setEditor(record)} aria-label={`Edit ${record.title}`}>Edit</button><button onClick={() => removeRecord(record)} aria-label={`Delete ${record.title}`}>Delete</button></div></td></tr>)}</tbody></table></div> : <div className="table-message"><span className="empty-sun">✳</span><strong>{query ? 'No matching records' : 'Your ledger is ready'}</strong><span>{query ? 'Try another word or clear your search.' : 'Add the first activity, cost, harvest or sale for this farm.'}</span>{!query && <button className="button button-primary" onClick={() => setEditor({})}>＋ Add your first record</button>}</div>}
      </section>
    </div>
  )
}
