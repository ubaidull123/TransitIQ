import { useState } from 'react'
import { ApiRequestError, createException, fieldErrors } from '../api'
import {
  EXCEPTION_SOURCES,
  SOURCE_LABELS,
  type ExceptionInput,
  type ExceptionRecord,
  type ExceptionSource,
} from '../types'

interface FieldProps {
  name: string
  label: string
  value: string
  onChange: (value: string) => void
  error?: string
  hint?: string
  multiline?: boolean
  type?: string
  placeholder?: string
  mono?: boolean
}

function Field({
  name,
  label,
  value,
  onChange,
  error,
  hint,
  multiline,
  type = 'text',
  placeholder,
  mono,
}: FieldProps) {
  const id = `field-${name}`
  const describedBy = [
    error ? `${id}-error` : null,
    hint && !error ? `${id}-hint` : null,
  ]
    .filter(Boolean)
    .join(' ')

  const className = [
    'control',
    multiline ? 'control--area' : null,
    mono && !multiline ? 'control--stamp' : null,
    error ? 'control--invalid' : null,
  ]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="field">
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      {multiline ? (
        <textarea
          id={id}
          name={name}
          className={className}
          value={value}
          rows={3}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy || undefined}
        />
      ) : (
        <input
          id={id}
          name={name}
          type={type}
          className={className}
          value={value}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy || undefined}
        />
      )}
      {hint && !error && (
        <p className="field__hint" id={`${id}-hint`}>
          {hint}
        </p>
      )}
      {error && (
        <p className="field__error" id={`${id}-error`}>
          {error}
        </p>
      )}
    </div>
  )
}

function localStamp(): string {
  const now = new Date()
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 16)
}

interface Props {
  onCreated: (record: ExceptionRecord) => void
}

export default function ExceptionForm({ onCreated }: Props) {
  const [shipmentId, setShipmentId] = useState('')
  const [source, setSource] = useState<ExceptionSource>('manual')
  const [reportedAt, setReportedAt] = useState(localStamp)
  const [carrier, setCarrier] = useState('')
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [rawText, setRawText] = useState('')
  const [metadataText, setMetadataText] = useState('')

  const [errors, setErrors] = useState<Record<string, string>>({})
  const [banner, setBanner] = useState<string | null>(null)
  const [confirmation, setConfirmation] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  function reset() {
    setShipmentId('')
    setCarrier('')
    setOrigin('')
    setDestination('')
    setRawText('')
    setMetadataText('')
    setReportedAt(localStamp())
    setSource('manual')
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setErrors({})
    setBanner(null)

    if (!reportedAt) {
      setErrors({ reported_at: 'Enter when the exception was reported.' })
      return
    }

    let metadata: Record<string, unknown> | null = null
    if (metadataText.trim()) {
      let parsed: unknown
      try {
        parsed = JSON.parse(metadataText)
      } catch {
        setErrors({ metadata: 'That is not valid JSON.' })
        return
      }
      if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
        setErrors({ metadata: 'Metadata has to be a JSON object, like {"hold_code": "C1"}.' })
        return
      }
      metadata = parsed as Record<string, unknown>
    }

    const payload: ExceptionInput = {
      shipment_id: shipmentId.trim(),
      source,
      reported_at: new Date(reportedAt).toISOString(),
      carrier: carrier.trim(),
      origin: origin.trim(),
      destination: destination.trim(),
      raw_text: rawText,
      metadata,
    }

    setSubmitting(true)
    try {
      const record = await createException(payload)
      onCreated(record)
      setConfirmation(`Recorded as #${record.id}.`)
      reset()
    } catch (error) {
      if (error instanceof ApiRequestError) {
        const mapped = fieldErrors(error)
        if (error.status === 409) {
          setErrors({ shipment_id: error.message })
        } else if (Object.keys(mapped).length > 0) {
          setErrors(mapped)
        } else {
          setBanner(error.message)
        }
      } else {
        setBanner('The exception could not be recorded. Try again.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      {banner && <p className="notice">{banner}</p>}
      {confirmation && (
        <p className="notice notice--calm" role="status">
          {confirmation}
        </p>
      )}

      <Field
        name="shipment_id"
        label="Shipment ID"
        value={shipmentId}
        onChange={(value) => setShipmentId(value)}
        error={errors.shipment_id}
        placeholder="SHP-10001"
        mono
      />

      <div className="field">
        <label className="field__label" htmlFor="field-source">
          Source
        </label>
        <select
          id="field-source"
          name="source"
          className="control"
          value={source}
          onChange={(event) => setSource(event.target.value as ExceptionSource)}
        >
          {EXCEPTION_SOURCES.map((option) => (
            <option key={option} value={option}>
              {SOURCE_LABELS[option]}
            </option>
          ))}
        </select>
      </div>

      <Field
        name="reported_at"
        label="Reported at"
        type="datetime-local"
        value={reportedAt}
        onChange={setReportedAt}
        error={errors.reported_at}
      />

      <Field
        name="carrier"
        label="Carrier"
        value={carrier}
        onChange={setCarrier}
        error={errors.carrier}
        placeholder="Maersk"
      />

      <div className="pair">
        <Field
          name="origin"
          label="Origin"
          value={origin}
          onChange={setOrigin}
          error={errors.origin}
          placeholder="Ningbo"
        />
        <Field
          name="destination"
          label="Destination"
          value={destination}
          onChange={setDestination}
          error={errors.destination}
          placeholder="Rotterdam"
        />
      </div>

      <Field
        name="raw_text"
        label="What happened"
        value={rawText}
        onChange={setRawText}
        error={errors.raw_text}
        placeholder="Vessel held at transshipment port; 4 days behind schedule."
        multiline
      />

      <Field
        name="metadata"
        label="Metadata"
        value={metadataText}
        onChange={setMetadataText}
        error={errors.metadata}
        hint="Optional JSON object."
        placeholder={'{"hold_code": "C1"}'}
        multiline
      />

      <button className="submit" type="submit" disabled={submitting}>
        {submitting ? 'Recording…' : 'Record exception'}
      </button>
    </form>
  )
}