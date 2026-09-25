import type { AnalysisRecord } from '../types'

const stamp = new Intl.DateTimeFormat(undefined, {
  day: '2-digit',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
  hourCycle: 'h23',
})

interface Props {
  analysis: AnalysisRecord | null
  loading: boolean
  error: string | null
  running: boolean
  onRun: () => void
}

function listOrNone(items: string[]) {
  if (items.length === 0) {
    return <p className="output__none">None recorded</p>
  }
  return (
    <ul className="output__list">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}

export default function AnalysisPanel({ analysis, loading, error, running, onRun }: Props) {
  if (!analysis && !loading && !error) {
    return null
  }

  const runs = analysis?.analysis_history.length ?? 0

  return (
    <section className="output" aria-live="polite">
      <div className="output__head">
        <h2 className="output__title">Agent output</h2>
        {analysis && <span className="output__id">{analysis.shipment_id}</span>}
      </div>

      {loading && <p className="placeholder">Loading analysis…</p>}

      {error && <p className="notice">{error}</p>}

      {analysis && !loading && !error && (
        <>
          <dl className="output__fields">
            <div className="output__field">
              <dt className="output__label">Status</dt>
              <dd className="output__value">{analysis.status}</dd>
            </div>
            <div className="output__field">
              <dt className="output__label">Step</dt>
              <dd className="output__value">{analysis.current_step}</dd>
            </div>
            <div className="output__field">
              <dt className="output__label">Exception type</dt>
              <dd className="output__value">{analysis.exception_type ?? '—'}</dd>
            </div>
            <div className="output__field">
              <dt className="output__label">Severity</dt>
              <dd className="output__value">{analysis.severity ?? '—'}</dd>
            </div>
            <div className="output__field">
              <dt className="output__label">Updated</dt>
              <dd className="output__value output__value--stamp">
                {analysis.updated_at ? stamp.format(new Date(analysis.updated_at)) : '—'}
              </dd>
            </div>
          </dl>

          <div className="output__block">
            <h3 className="output__subtitle">Missing information</h3>
            {listOrNone(analysis.missing_information)}
          </div>

          <div className="output__block">
            <h3 className="output__subtitle">Recommended actions</h3>
            {listOrNone(analysis.recommended_actions)}
          </div>

          {analysis.actions.length > 0 && (
            <div className="output__block">
              <h3 className="output__subtitle">Actions</h3>
              <table className="output__actions">
                <thead>
                  <tr>
                    <th scope="col">ID</th>
                    <th scope="col">Action</th>
                    <th scope="col">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {analysis.actions.map((action) => (
                    <tr key={action.id}>
                      <td className="cell--id">{action.id}</td>
                      <td>{action.description ?? '—'}</td>
                      <td>{action.status ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="output__count">
            {runs} analysis run{runs === 1 ? '' : 's'} recorded
          </p>

          {analysis.analysis_error ? (
            <p className="notice">
              Analysis failed: {analysis.analysis_error}
            </p>
          ) : (
            analysis.status === 'new' && (
              <p className="notice notice--calm">
                Not analysed yet. Run the agent to produce output for this shipment.
              </p>
            )
          )}

          <div className="output__footer">
            <button className="submit" type="button" onClick={onRun} disabled={running}>
              {running ? 'Running…' : 'Run analysis'}
            </button>
          </div>
        </>
      )}
    </section>
  )
}