import { useCallback, useEffect, useRef, useState } from 'react'
import { readOutbox } from '../offline/db.js'
import { syncPendingChanges } from '../offline/sync.js'

export default function SyncStatus({ token, userId }) {
  const [online, setOnline] = useState(navigator.onLine)
  const [pending, setPending] = useState(0)
  const [busy, setBusy] = useState(false)
  const [failed, setFailed] = useState(false)
  const busyRef = useRef(false)

  const refresh = useCallback(async () => {
    try { setPending((await readOutbox(userId)).length) } catch { setPending(0) }
  }, [userId])

  const sync = useCallback(async () => {
    if (!navigator.onLine || busyRef.current) return
    busyRef.current = true
    setBusy(true)
    setFailed(false)
    try {
      const count = await syncPendingChanges(token, userId)
      await refresh()
      if (count) window.dispatchEvent(new Event('farm:sync-complete'))
    } catch {
      setFailed(true)
      await refresh()
    } finally {
      busyRef.current = false
      setBusy(false)
    }
  }, [refresh, token, userId])

  useEffect(() => {
    const onlineAgain = () => { setOnline(true); sync() }
    const offlineNow = () => setOnline(false)
    const queued = () => refresh()
    window.addEventListener('online', onlineAgain)
    window.addEventListener('offline', offlineNow)
    window.addEventListener('farm:queue-changed', queued)
    refresh()
    if (navigator.onLine) sync()
    return () => {
      window.removeEventListener('online', onlineAgain)
      window.removeEventListener('offline', offlineNow)
      window.removeEventListener('farm:queue-changed', queued)
    }
  }, [refresh, sync])

  const label = !online ? `Offline · ${pending} waiting` : busy ? 'Syncing…' : failed ? `${pending} waiting · retry` : pending ? `${pending} to sync` : 'Synced'
  return (
    <button className={`sync-chip ${online ? 'sync-online' : 'sync-offline'} ${failed ? 'sync-failed' : ''}`} onClick={sync} disabled={!online || busy || !pending} title={failed ? 'Could not sync. Your saved entries remain on this device.' : 'Farm record synchronization status'}>
      <span className="sync-dot" />{label}
    </button>
  )
}
