import { useState } from 'react'

const categories = [
  ['planting', 'Planting'],
  ['inputs', 'Farm inputs'],
  ['labour', 'Labour'],
  ['expenses', 'Other expenses'],
  ['harvest', 'Harvest'],
  ['sales', 'Sales'],
]

function localDate() {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

export default function RecordForm({ initial, onSubmit, onCancel, saving }) {
  const [form, setForm] = useState(() => ({
    title: initial?.title || '',
    category: initial?.category || 'planting',
    occurred_on: initial?.occurred_on || localDate(),
    notes: initial?.notes || '',
    quantity: initial?.quantity ?? '',
    unit: initial?.unit || '',
    amount: initial?.amount ?? '',
  }))

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function submit(event) {
    event.preventDefault()
    onSubmit({
      ...form,
      quantity: form.quantity === '' ? null : Number(form.quantity),
      amount: form.amount === '' ? null : Number(form.amount),
    })
  }

  return (
    <form className="record-form" onSubmit={submit}>
      <div className="form-grid">
        <label className="field span-two">What happened?
          <input autoFocus value={form.title} onChange={(event) => update('title', event.target.value)} required maxLength="160" placeholder="e.g. Bought fertilizer for the main plot" />
        </label>
        <label className="field">Record type
          <select value={form.category} onChange={(event) => update('category', event.target.value)}>{categories.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select>
        </label>
        <label className="field">Date
          <input type="date" value={form.occurred_on} onChange={(event) => update('occurred_on', event.target.value)} required />
        </label>
        <label className="field">Quantity <span className="optional">optional</span>
          <input type="number" min="0" step="0.01" value={form.quantity} onChange={(event) => update('quantity', event.target.value)} placeholder="0.00" />
        </label>
        <label className="field">Unit <span className="optional">optional</span>
          <input value={form.unit} onChange={(event) => update('unit', event.target.value)} maxLength="40" placeholder="kg, bags, hours…" />
        </label>
        <label className="field span-two">Amount (KES) <span className="optional">optional</span>
          <input type="number" min="0" step="0.01" value={form.amount} onChange={(event) => update('amount', event.target.value)} placeholder="0.00" />
        </label>
        <label className="field span-two">Notes <span className="optional">optional</span>
          <textarea rows="3" value={form.notes} onChange={(event) => update('notes', event.target.value)} maxLength="4000" placeholder="Add details that will help you remember this activity." />
        </label>
      </div>
      <div className="form-actions"><button type="button" className="button button-quiet" onClick={onCancel}>Cancel</button><button type="submit" className="button button-primary" disabled={saving}>{saving ? 'Saving…' : initial ? 'Save changes' : 'Save record'}</button></div>
    </form>
  )
}
