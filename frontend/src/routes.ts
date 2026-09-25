const SHIPMENT_PREFIX = '#/shipments/'

export type Route = { view: 'ledger' } | { view: 'agent'; shipmentId: string }

export function parseRoute(hash: string): Route {
  if (hash.startsWith(SHIPMENT_PREFIX)) {
    const shipmentId = decodeURIComponent(hash.slice(SHIPMENT_PREFIX.length)).trim()
    if (shipmentId) {
      return { view: 'agent', shipmentId }
    }
  }
  return { view: 'ledger' }
}

export function agentPath(shipmentId: string): string {
  return `${SHIPMENT_PREFIX}${encodeURIComponent(shipmentId)}`
}

export const LEDGER_PATH = '#/'