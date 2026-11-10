const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

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
  const monthly = MONTH_NAMES.map((label, index) => {
    const month = index + 1
    const monthItems = items.filter((record) => Number(record.occurred_on.slice(5, 7)) === month)
    const monthExpenses = sumAmount(monthItems.filter((record) => costs.has(record.category)))
    const monthSales = sumAmount(monthItems.filter((record) => record.category === 'sales'))
    return {
      month,
      label,
      expenses: monthExpenses,
      sales: monthSales,
      profit: monthSales - monthExpenses,
      record_count: monthItems.length,
    }
  })
  return {
    year,
    record_count: items.length,
    expenses,
    sales,
    profit: sales - expenses,
    harvest_quantities: [...harvest.entries()].map(([unit, quantity]) => ({ unit, quantity })),
    categories: [...grouped.entries()].map(([name, values]) => ({ name, ...values })),
    monthly,
    recent_records: items.slice(0, 5).map((record) => ({
      id: record.id,
      title: record.title,
      category: record.category_label,
      occurred_on: record.occurred_on,
      amount: record.amount,
    })),
  }
}
