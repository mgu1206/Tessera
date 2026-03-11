import { Ticket, TicketCreateRequest } from '../types'

const BASE = '/api/tickets'

export async function listTickets(): Promise<Ticket[]> {
  const res = await fetch(BASE)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function createTicket(data: TicketCreateRequest): Promise<Ticket> {
  const res = await fetch(BASE, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || '예매 요청 실패')
  }
  return res.json()
}

export async function cancelTicket(ticketId: string): Promise<void> {
  const res = await fetch(`${BASE}/${ticketId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await res.text())
}
