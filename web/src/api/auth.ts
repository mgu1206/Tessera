export async function getAuthStatus(): Promise<{ logged_in: boolean; srt_id: string | null }> {
  const res = await fetch('/api/auth/status')
  if (!res.ok) throw new Error('인증 상태 확인 실패')
  return res.json()
}

export async function srtLogin(srt_id: string, srt_password: string): Promise<void> {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ srt_id, srt_password }),
  })
  if (!res.ok) {
    const err = await res.json()
    throw new Error(err.detail || 'SRT 로그인 실패')
  }
}

export async function srtLogout(): Promise<void> {
  const res = await fetch('/api/auth/logout', { method: 'POST' })
  if (!res.ok) throw new Error('로그아웃 실패')
}
