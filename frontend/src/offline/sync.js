import { api } from '../services/api.js'
import { finishSync, readOutbox } from './db.js'

export async function syncPendingChanges(token, userId) {
  if (!navigator.onLine) return 0
  const operations = await readOutbox(userId)
  if (!operations.length) return 0
  let synced = 0
  for (let offset = 0; offset < operations.length; offset += 100) {
    const batch = operations.slice(offset, offset + 100)
    const response = await api('/records/sync', {
      token,
      method: 'POST',
      body: { operations: batch.map(({ sequence, ...operation }) => operation) },
    })
    await finishSync(response.results, userId)
    synced += response.results.length
  }
  return synced
}
