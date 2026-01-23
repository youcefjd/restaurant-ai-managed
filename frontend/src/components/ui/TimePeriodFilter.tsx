type TimePeriod = 7 | 30 | 90

interface TimePeriodFilterProps {
  value: TimePeriod
  onChange: (period: TimePeriod) => void
}

export default function TimePeriodFilter({ value, onChange }: TimePeriodFilterProps) {
  const periods: TimePeriod[] = [7, 30, 90]

  return (
    <div className="flex gap-1">
      {periods.map((period) => (
        <button
          key={period}
          onClick={() => onChange(period)}
          className={`btn btn-sm ${value === period ? 'btn-primary' : 'btn-secondary'}`}
        >
          {period}d
        </button>
      ))}
    </div>
  )
}
