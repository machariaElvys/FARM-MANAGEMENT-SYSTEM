import { useCallback, useEffect, useState } from 'react'
import { api } from '../services/api.js'

const PAGE_SIZE = 25

export default function AdminPage({ token }) {
  const [overview, setOverview] = useState(null)
  const [page, setPage] = useState({ items: [], total: 0 })
  const [search, setSearch] = useState('')
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingId, setUpdatingId] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ limit: String(PAGE_SIZE), offset: String(offset) })
      if (search.trim()) params.set('search', search.trim())
      const [nextOverview, nextPage] = await Promise.all([
        api('/admin/overview', { token }),
        api(`/admin/users?${params.toString()}`, { token }),
      ])
      setOverview(nextOverview)
      setPage(nextPage)
      setError('')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setLoading(false)
    }
  }, [offset, search, token])

  useEffect(() => { load() }, [load])

  async function changeStatus(user) {
    const nextStatus = !user.is_active
    const action = nextStatus ? 'reactivate' : 'suspend'
    if (!window.confirm(`${action === 'suspend' ? 'Suspend' : 'Reactivate'} ${user.name}'s account?`)) return
    setUpdatingId(user.id)
    try {
      await api(`/admin/users/${encodeURIComponent(user.id)}/status`, {
        token,
        method: 'PATCH',
        body: { is_active: nextStatus },
      })
      await load()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setUpdatingId('')
    }
  }

  const firstRow = page.total ? offset + 1 : 0
  const lastRow = Math.min(offset + PAGE_SIZE, page.total)

  return (
    <div className="page-stack">
      <section className="page-heading">
        <div><span className="eyebrow">SYSTEM ADMINISTRATION</span><h1>Administration</h1><p>Monitor farmer accounts and activity across Shamba Ledger.</p></div>
        <button className="button button-quiet" disabled={loading} onClick={load}>{loading ? 'Refreshing…' : 'Refresh'}</button>
      </section>
      {error && <p className="inline-error" role="alert">{error}</p>}

      <section className="admin-summary-grid" aria-label="System overview">
        <AdminMetric label="User accounts" value={overview?.total_users ?? '—'} />
        <AdminMetric label="Active accounts" value={overview?.active_users ?? '—'} />
        <AdminMetric label="Farm records" value={overview?.total_records ?? '—'} />
        <AdminMetric label="Records this year" value={overview?.records_this_year ?? '—'} />
      </section>

      <section className="panel table-panel">
        <div className="table-toolbar">
          <div className="record-count"><strong>Accounts</strong> <span>· {loading ? 'Loading…' : `${firstRow}–${lastRow} of ${page.total}`}</span></div>
          <label className="search-box"><span aria-hidden="true">⌕</span><input aria-label="Search accounts" value={search} onChange={(event) => { setSearch(event.target.value); setOffset(0) }} placeholder="Search name or email" /></label>
        </div>
        {page.items.length ? (
          <div className="table-scroll">
            <table>
              <thead><tr><th>Account</th><th>Role</th><th>Records</th><th>Joined</th><th>Status</th><th><span className="sr-only">Actions</span></th></tr></thead>
              <tbody>{page.items.map((user) => (
                <tr key={user.id}>
                  <td><div className="table-title">{user.name}</div><div className="table-subtitle">{user.email}</div></td>
                  <td><span className={`admin-role ${user.role === 'admin' ? 'admin-role-elevated' : ''}`}>{user.role}</span></td>
                  <td>{user.record_count}</td>
                  <td>{formatDate(user.created_at)}</td>
                  <td><span className={`account-status ${user.is_active ? 'account-status-active' : 'account-status-inactive'}`}>{user.is_active ? 'Active' : 'Suspended'}</span></td>
                  <td><div className="row-actions">{user.role === 'admin' ? <span className="admin-protected">Protected</span> : <button className="admin-action" disabled={loading || updatingId === user.id} onClick={() => changeStatus(user)}>{updatingId === user.id ? 'Saving…' : user.is_active ? 'Suspend' : 'Reactivate'}</button>}</div></td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        ) : (
          <div className="table-message"><span className="empty-sun">✳</span><strong>{loading ? 'Loading accounts…' : 'No accounts found'}</strong><span>{search ? 'Try another name or email address.' : 'Accounts will appear here after farmers register.'}</span></div>
        )}
        <div className="admin-pagination">
          <span>Showing {firstRow}–{lastRow} of {page.total}</span>
          <div><button className="button button-quiet" disabled={offset === 0 || loading} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Previous</button><button className="button button-quiet" disabled={offset + PAGE_SIZE >= page.total || loading} onClick={() => setOffset(offset + PAGE_SIZE)}>Next</button></div>
        </div>
      </section>
      <p className="report-footnote">Administrator accounts are protected from status changes on this page.</p>
    </div>
  )
}

function AdminMetric({ label, value }) {
  return <article className="report-card"><span>{label}</span><strong>{value}</strong></article>
}

function formatDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat('en-KE', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(value))
}
