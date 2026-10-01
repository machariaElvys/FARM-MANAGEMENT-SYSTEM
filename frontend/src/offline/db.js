const DATABASE_NAME = 'shamba-ledger'
const DATABASE_VERSION = 2

const databasePromises = new Map()

function openDatabase(userId) {
  if (!userId) return Promise.reject(new Error('A signed-in farmer is required for local storage.'))
  if (databasePromises.has(userId)) return databasePromises.get(userId)
  const databasePromise = new Promise((resolve, reject) => {
    const request = indexedDB.open(`${DATABASE_NAME}-${userId}`, DATABASE_VERSION)
    request.onupgradeneeded = () => {
      const db = request.result
      if (!db.objectStoreNames.contains('records')) db.createObjectStore('records', { keyPath: 'id' })
      if (!db.objectStoreNames.contains('operations')) db.createObjectStore('operations', { keyPath: 'sequence', autoIncrement: true })
    }
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error || new Error('Could not open local farm storage.'))
  })
  databasePromises.set(userId, databasePromise)
  return databasePromise
}

function requestResult(request) {
  return new Promise((resolve, reject) => {
    request.onsuccess = () => resolve(request.result)
    request.onerror = () => reject(request.error || new Error('Local storage request failed.'))
  })
}

export async function readRecords(userId) {
  const db = await openDatabase(userId)
  const tx = db.transaction('records', 'readonly')
  const records = await requestResult(tx.objectStore('records').getAll())
  return records.sort((a, b) => b.occurred_on.localeCompare(a.occurred_on))
}

export async function replaceServerRecords(records, userId) {
  const existing = await readRecords(userId)
  const pending = existing.filter((record) => record.sync_state === 'pending')
  const db = await openDatabase(userId)
  const tx = db.transaction('records', 'readwrite')
  const store = tx.objectStore('records')
  store.clear()
  for (const record of records) store.put({ ...record, sync_state: 'synced' })
  const serverIds = new Set(records.map((record) => record.id))
  for (const record of pending) if (!serverIds.has(record.id)) store.put(record)
  return new Promise((resolve, reject) => {
    tx.oncomplete = resolve
    tx.onerror = () => reject(tx.error || new Error('Could not update the local farm cache.'))
  })
}

export async function savePendingRecord(record, userId) {
  const db = await openDatabase(userId)
  const tx = db.transaction(['records', 'operations'], 'readwrite')
  const localRecord = { ...record, sync_state: 'pending' }
  tx.objectStore('records').put(localRecord)
  tx.objectStore('operations').add({
    operation_id: crypto.randomUUID(),
    action: 'upsert',
    record_id: record.id,
    record: {
      id: record.id,
      title: record.title,
      category: record.category,
      occurred_on: record.occurred_on,
      notes: record.notes,
      quantity: record.quantity,
      unit: record.unit,
      amount: record.amount,
    },
  })
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(localRecord)
    tx.onerror = () => reject(tx.error || new Error('Could not save this entry on the device.'))
  })
}

export async function queueRecordDelete(recordId, userId) {
  const db = await openDatabase(userId)
  const tx = db.transaction(['records', 'operations'], 'readwrite')
  tx.objectStore('records').delete(recordId)
  tx.objectStore('operations').add({
    operation_id: crypto.randomUUID(),
    action: 'delete',
    record_id: recordId,
  })
  return new Promise((resolve, reject) => {
    tx.oncomplete = resolve
    tx.onerror = () => reject(tx.error || new Error('Could not queue this deletion.'))
  })
}

export async function readOutbox(userId) {
  const db = await openDatabase(userId)
  const tx = db.transaction('operations', 'readonly')
  const operations = await requestResult(tx.objectStore('operations').getAll())
  return operations.sort((a, b) => a.sequence - b.sequence)
}

export async function finishSync(results, userId) {
  const queued = await readOutbox(userId)
  const sequenceById = new Map(queued.map((operation) => [operation.operation_id, operation.sequence]))
  const db = await openDatabase(userId)
  const tx = db.transaction(['records', 'operations'], 'readwrite')
  const records = tx.objectStore('records')
  const operations = tx.objectStore('operations')
  for (const result of results) {
    const sequence = sequenceById.get(result.operation_id)
    if (sequence !== undefined) operations.delete(sequence)
    if (result.action === 'delete') records.delete(result.record_id)
    else if (result.record) records.put({ ...result.record, sync_state: 'synced' })
  }
  return new Promise((resolve, reject) => {
    tx.oncomplete = resolve
    tx.onerror = () => reject(tx.error || new Error('Could not finish syncing local changes.'))
  })
}
