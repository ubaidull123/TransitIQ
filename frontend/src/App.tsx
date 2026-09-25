import { useCallback, useEffect, useState } from 'react'
import { LIST_LIMIT, listExceptions } from './api'
import AgentPage from './components/AgentPage'
import ExceptionForm from './components/ExceptionForm'
import LedgerPage from './components/LedgerPage'
import { agentPath, parseRoute, type Route } from './routes'
import type { ExceptionRecord } from './types'

const HIGHLIGHT_MS = 4000

export default function App() {
  const [records, setRecords] = useState<ExceptionRecord[]>([])
  const [loaded, setLoaded] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [highlightId, setHighlightId] = useState<number | null>(null)
  const [route, setRoute] = useState<Route>(() => parseRoute(window.location.hash))

  useEffect(() => {
    const handleHashChange = () => setRoute(parseRoute(window.location.hash))
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const refresh = useCallback(async () => {
    try {
      setRecords(await listExceptions())
      setLoadError(null)
    } catch (error) {
      setLoadError(
        error instanceof Error ? error.message : 'The exception list could not be loaded.',
      )
    } finally {
      setLoaded(true)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    if (highlightId === null) {
      return
    }
    const timer = window.setTimeout(() => setHighlightId(null), HIGHLIGHT_MS)
    return () => window.clearTimeout(timer)
  }, [highlightId])

  const handleCreated = useCallback(
    async (record: ExceptionRecord) => {
      setHighlightId(record.id)
      await refresh()
    },
    [refresh],
  )

  const openAgent = useCallback((shipmentId: string) => {
    window.location.hash = agentPath(shipmentId)
  }, [])

  const capped = records.length >= LIST_LIMIT
  const isAgent = route.view === 'agent'

  return (
    <div className={isAgent ? 'shell shell--agent' : 'shell'}>
      <header className="bar">
        <div className="bar__identity">
          <h1 className="bar__name">TransitIQ</h1>
          <span className="bar__role">{isAgent ? 'Agent view' : 'Exception intake'}</span>
        </div>
        <p className="bar__readout">
          <strong className="bar__count">
            {records.length}
            {capped ? '+' : ''}
          </strong>{' '}
          on file
        </p>
      </header>

      {!isAgent && (
        <section className="rail">
          <h2 className="rail__title">Record an exception</h2>
          <ExceptionForm onCreated={handleCreated} />
        </section>
      )}

      {route.view === 'agent' ? (
        <AgentPage shipmentId={route.shipmentId} />
      ) : (
        <LedgerPage
          records={records}
          loaded={loaded}
          error={loadError}
          highlightId={highlightId}
          onOpenAgent={openAgent}
        />
      )}
    </div>
  )
}