import { LIST_LIMIT } from '../api'
import { SOURCE_LABELS, type ExceptionRecord, type ExceptionSource } from '../types'

const stamp = new Intl.DateTimeFormat(undefined, {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})

interface Props {
  records: ExceptionRecord[]
  loaded: boolean
  error: string | null
  highlightId: number | null
  selectedId: number | null
  onSelect: (record: ExceptionRecord) => void
  onAnalyze: (record: ExceptionRecord) => void
}

export default function ExceptionTable({
  records,
  loaded,
  error,
  highlightId,
  selectedId,
  onSelect,
  onAnalyze,
}: Props) {
  const capped = records.length >= LIST_LIMIT

  return (
    <>
      <div className="ledger__head">
        <h2 className="ledger__title">Exceptions on file</h2>
        {capped && (
          <p className="ledger__note">
            Showing the {LIST_LIMIT} most recent. Older exceptions are not listed.
          </p>
        )}
      </div>

      {error && <p className="notice">{error}</p>}

      {!error && !loaded && <p className="placeholder">Loading exceptions…</p>}

      {!error && loaded && records.length === 0 && (
        <p className="placeholder">
          No exceptions on file yet. Record the first one with the form.
        </p>
      )}

      {!error && records.length > 0 && (
        <div className="ledger__scroll">
          <table className="ledger__table">
            <thead>
              <tr>
                <th scope="col">Shipment</th>
                <th scope="col">Route</th>
                <th scope="col">Carrier</th>
                <th scope="col">Source</th>
                <th scope="col">Reported</th>
                <th scope="col">Exception</th>
                <th scope="col">Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map((record) => {
                const isSelected = record.id === selectedId
                const classes = ['row', 'row--selectable']
                if (record.id === highlightId) {
                  classes.push('row--new')
                }
                if (isSelected) {
                  classes.push('row--selected')
                }
                return (
                  <tr
                    key={record.id}
                    className={classes.join(' ')}
                    tabIndex={0}
                    aria-selected={isSelected}
                    onClick={() => onSelect(record)}
                    onKeyDown={(event) => {
                      if (event.target !== event.currentTarget) {
                        return
                      }
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        onSelect(record)
                      }
                    }}
                  >
                    <td className="cell--id">{record.shipment_id}</td>
                    <td className="cell--route">
                      {record.origin} → {record.destination}
                    </td>
                    <td className="cell--carrier">{record.carrier}</td>
                    <td className="cell--source">
                      {SOURCE_LABELS[record.source as ExceptionSource] ?? record.source}
                    </td>
                    <td className="cell--stamp">
                      {stamp.format(new Date(record.reported_at))}
                    </td>
                    <td className="cell--text" title={record.raw_text}>
                      {record.raw_text}
                    </td>
                    <td className="cell--action">
                      {isSelected && (
                        <button
                          type="button"
                          className="runlink"
                          onClick={(event) => {
                            event.stopPropagation()
                            onAnalyze(record)
                          }}
                        >
                          Analyze →
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}