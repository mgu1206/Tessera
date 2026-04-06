import { TicketGroup } from '../types'

export async function listGroups(): Promise<TicketGroup[]> {
  const res = await fetch('/api/groups')
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function deleteGroup(groupId: string): Promise<void> {
  const res = await fetch(`/api/groups/${encodeURIComponent(groupId)}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(await res.text())
}
