export function summarizeRecords(records, year) {
  const items = records.filter((record) => record.occurred_on.startsWith(`${year}-`))
  const costs = new Set(['inputs', 'labour', 'expenses'])
  const sumAmount = (list) => list.reduce((sum, record) => sum + Number(record.amount || 0), 0)
  const expenses = sumAmount(items.filter((record) => costs.has(record.category)))
  const sales = sumAmount(items.filter((record) => record.category === 'sales'))
  const harvest = new Map()
  for (const record of items) {
    if (record.category !== 'harvest' || record.quantity == null) continue
    const unit = record.unit?.trim() || 'unspecified unit'
    harvest.set(unit, (harvest.get(unit) || 0) + Number(record.quantity))
  }
  const grouped = new Map()
  for (const record of items) {
    const current = grouped.get(record.category) || { label: record.category_label, count: 0, amount: 0 }
    current.count += 1
    current.amount += Number(record.amount || 0)
    grouped.set(record.category, current)
  }
  return {
    year,
    record_count: items.length,
    expenses,
    sales,
    harvest_quantities: [...harvest.entries()].map(([unit, quantity]) => ({ unit, quantity })),
    categories: [...grouped.entries()].map(([name, values]) => ({ name, ...values })),
    recent_records: items.slice(0, 5).map((record) => ({
      id: record.id,
      title: record.title,
      category: record.category_label,
      occurred_on: record.occurred_on,
      amount: record.amount,
    })),
  }
}
