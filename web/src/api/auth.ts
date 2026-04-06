export async function getAuthStatus(): Promise<{
  logged_in: boolean
  srt_id: string | null
  ktx_logged_in: boolean
  ktx_id: string | null
}> {
  const res = await fetch('/api/auth/status')
  if (!res.ok) throw new Error('인증 상태 확인 실패')
  return res.json()
}

export async function srtLogin(srt_id: string, srt_password: string): Promise<void> {
  let res: Response
  try {
    res = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ srt_id, srt_password }),
    })
  } catch {
    throw new Error('서버에 연결할 수 없습니다. 네트워크 상태를 확인하세요.')
  }
  if (!res.ok) {
    let detail = 'SRT 로그인 실패'
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch { /* non-JSON */ }
    throw new Error(detail)
  }
}

export async function srtLogout(): Promise<void> {
  const res = await fetch('/api/auth/logout', { method: 'POST' })
  if (!res.ok) throw new Error('로그아웃 실패')
}

export async function ktxLogin(ktx_id: string, ktx_password: string): Promise<void> {
  let res: Response
  try {
    res = await fetch('/api/auth/ktx/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ktx_id, ktx_password }),
    })
  } catch {
    throw new Error('서버에 연결할 수 없습니다.')
  }
  if (!res.ok) {
    let detail = 'KTX 로그인 실패'
    try {
      const err = await res.json()
      detail = err.detail || detail
    } catch { /* non-JSON */ }
    throw new Error(detail)
  }
}

export async function ktxLogout(): Promise<void> {
  const res = await fetch('/api/auth/ktx/logout', { method: 'POST' })
  if (!res.ok) throw new Error('KTX 로그아웃 실패')
}
