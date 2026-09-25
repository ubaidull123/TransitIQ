import { useState } from 'react'
import ExceptionTable from './ExceptionTable'
import type { ExceptionRecord } from '../types'

interface Props {
  records: ExceptionRecord[]
  loaded: boolean
  error: string | null
  highlightId: number | null
  onOpenAgent: (shipmentId: string) => void
}

export default function LedgerPage({
  records,
  loaded,
  error,
  highlightId,
  onOpenAgent,
}: Props) {
  const [selected, setSelected] = useState<ExceptionRecord | null>(null)

  return (
    <section className="ledger">
      <ExceptionTable
        records={records}
        loaded={loaded}
        error={error}
        highlightId={highlightId}
        selectedId={selected?.id ?? null}
        onSelect={setSelected}
        onAnalyze={(record) => onOpenAgent(record.shipment_id)}
      />
    </section>
  )
}