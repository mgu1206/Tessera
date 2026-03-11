import { useState } from 'react'
import { srtLogin } from '../api/auth'

interface Props {
  onLogin: (srtId: string) => void
}

export function LoginPage({ onLogin }: Props) {
  const [srtId, setSrtId] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!srtId.trim() || !password.trim()) return
    setLoading(true)
    setError('')
    try {
      await srtLogin(srtId.trim(), password.trim())
      onLogin(srtId.trim())
    } catch (err: any) {
      setError(err.message || 'SRT 로그인 실패')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">Tessera</h1>
        <p className="login-subtitle">SRT 자동 예매</p>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>SRT 회원번호 / 이메일</label>
            <input
              type="text"
              value={srtId}
              onChange={(e) => setSrtId(e.target.value)}
              placeholder="회원번호 또는 이메일"
              autoFocus
            />
          </div>
          <div className="form-group">
            <label>비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="비밀번호"
            />
          </div>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn-primary login-btn" disabled={loading}>
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>
      </div>
    </div>
  )
}
