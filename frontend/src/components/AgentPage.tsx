import { useCallback, useEffect, useState } from 'react'
import { getAnalysis, runAnalysis } from '../api'
import { LEDGER_PATH } from '../routes'
import AnalysisPanel from './AnalysisPanel'
import type { AnalysisRecord } from '../types'

interface Props {
  shipmentId: string
}

export default function AgentPage({ shipmentId }: Props) {
  const [analysis, setAnalysis] = useState<AnalysisRecord | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setAnalysis(await getAnalysis(shipmentId))
    } catch (cause) {
      setAnalysis(null)
      setError(
        cause instanceof Error ? cause.message : 'The analysis could not be loaded.',
      )
    } finally {
      setLoading(false)
    }
  }, [shipmentId])

  useEffect(() => {
    void load()
  }, [load])

  const handleRun = useCallback(async () => {
    setRunning(true)
    setError(null)
    try {
      setAnalysis(await runAnalysis(shipmentId))
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The analysis run failed.')
    } finally {
      setRunning(false)
    }
  }, [shipmentId])

  return (
    <section className="ledger">
      <div className="ledger__head">
        <h2 className="ledger__title">Agent</h2>
        <a className="backlink" href={LEDGER_PATH}>
          ← Back to ledger
        </a>
      </div>
      <AnalysisPanel
        analysis={analysis}
        loading={loading}
        error={error}
        running={running}
        onRun={() => {
          void handleRun()
        }}
      />
    </section>
  )
}