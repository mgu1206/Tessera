export interface AppSettings {
  telegram_enabled: boolean
  telegram_bot_token: string
  telegram_chat_id: string
  imessage_enabled: boolean
  imessage_recipients: string[]
  poll_interval_seconds: number
  report_interval_seconds: number
  max_attempts: number
}

export async function getSettings(): Promise<AppSettings> {
  const res = await fetch('/api/settings')
  if (!res.ok) throw new Error('설정 조회 실패')
  return res.json()
}

export async function updateSettings(data: AppSettings): Promise<AppSettings> {
  const res = await fetch('/api/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error('설정 저장 실패')
  return res.json()
}

export async function testTelegram(): Promise<void> {
  const res = await fetch('/api/settings/notifications/test/telegram', { method: 'POST' })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || '텔레그램 테스트 실패')
  }
}

export async function testImessage(): Promise<void> {
  const res = await fetch('/api/settings/notifications/test/imessage', { method: 'POST' })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'iMessage 테스트 실패')
  }
}

export async function getSystemInfo(): Promise<{ platform: string }> {
  const res = await fetch('/api/system/info')
  if (!res.ok) throw new Error('시스템 정보 조회 실패')
  return res.json()
}
