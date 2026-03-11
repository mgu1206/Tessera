import { Ticket } from '../types'

const EVENT_TYPES = [
  'ticket.created',
  'ticket.polling',
  'ticket.success',
  'ticket.failed',
  'ticket.cancelled',
  'ticket.deleted',
]

export function subscribeEvents(
  onEvent: (type: string, data: Ticket & { reason?: string }) => void
): () => void {
  const source = new EventSource('/api/events')

  EVENT_TYPES.forEach((type) => {
    source.addEventListener(type, (e) => {
      const data = JSON.parse((e as MessageEvent).data)
      onEvent(type, data)
    })
  })

  return () => source.close()
}
