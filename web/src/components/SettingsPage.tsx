import { useEffect, useState } from 'react'
import {
  AppSettings,
  getSettings,
  updateSettings,
  testTelegram,
  testImessage,
  getSystemInfo,
} from '../api/settings'
import { ktxLogin, ktxLogout, getAuthStatus } from '../api/auth'

interface Props {
  onBack: () => void
  onKtxStatusChange?: (loggedIn: boolean, ktxId: string | null) => void
}

export function SettingsPage({ onBack, onKtxStatusChange }: Props) {
  const [settings, setSettings] = useState<AppSettings>({
    telegram_enabled: false,
    telegram_bot_token: '',
    telegram_chat_id: '',
    imessage_enabled: false,
    imessage_recipients: [],
    poll_interval_seconds: 5,
    report_interval_seconds: 300,
    max_attempts: 0,
  })
  const [isMac, setIsMac] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testingTg, setTestingTg] = useState(false)
  const [testingIm, setTestingIm] = useState(false)
  const [message, setMessage] = useState('')

  // KTX auth state
  const [ktxLoggedIn, setKtxLoggedIn] = useState(false)
  const [ktxCurrentId, setKtxCurrentId] = useState<string | null>(null)
  const [ktxId, setKtxId] = useState('')
  const [ktxPassword, setKtxPassword] = useState('')
  const [ktxSaving, setKtxSaving] = useState(false)

  useEffect(() => {
    getSettings().then(setSettings).catch(() => {})
    getSystemInfo().then((info) => setIsMac(info.platform === 'Darwin')).catch(() => {})
    getAuthStatus().then((s) => {
      setKtxLoggedIn(s.ktx_logged_in)
      setKtxCurrentId(s.ktx_id)
    }).catch(() => {})
  }, [])

  async function handleSave() {
    setSaving(true)
    setMessage('')
    try {
      const updated = await updateSettings(settings)
      setSettings(updated)
      setMessage('저장 완료')
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : '저장 실패')
    } finally {
      setSaving(false)
    }
  }

  async function handleTestTelegram() {
    setTestingTg(true)
    setMessage('')
    try {
      await testTelegram()
      setMessage('텔레그램 테스트 전송 완료')
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : '실패')
    } finally {
      setTestingTg(false)
    }
  }

  async function handleTestImessage() {
    setTestingIm(true)
    setMessage('')
    try {
      await testImessage()
      setMessage('iMessage 테스트 전송 완료')
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : '실패')
    } finally {
      setTestingIm(false)
    }
  }

  async function handleKtxLogin() {
    if (!ktxId || !ktxPassword) {
      setMessage('KTX ID와 비밀번호를 입력하세요.')
      return
    }
    setKtxSaving(true)
    setMessage('')
    try {
      await ktxLogin(ktxId, ktxPassword)
      setKtxLoggedIn(true)
      setKtxCurrentId(ktxId)
      setKtxPassword('')
      setMessage('KTX 계정 등록 완료')
      onKtxStatusChange?.(true, ktxId)
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : 'KTX 로그인 실패')
    } finally {
      setKtxSaving(false)
    }
  }

  async function handleKtxLogout() {
    try {
      await ktxLogout()
      setKtxLoggedIn(false)
      setKtxCurrentId(null)
      setKtxId('')
      setKtxPassword('')
      setMessage('KTX 계정 해제 완료')
      onKtxStatusChange?.(false, null)
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : 'KTX 로그아웃 실패')
    }
  }

  function setRecipient(index: number, value: string) {
    setSettings((prev) => {
      const recipients = [...prev.imessage_recipients]
      recipients[index] = value
      return { ...prev, imessage_recipients: recipients }
    })
  }

  function addRecipient() {
    if (settings.imessage_recipients.length >= 5) return
    setSettings((prev) => ({
      ...prev,
      imessage_recipients: [...prev.imessage_recipients, ''],
    }))
  }

  function removeRecipient(index: number) {
    setSettings((prev) => ({
      ...prev,
      imessage_recipients: prev.imessage_recipients.filter((_, i) => i !== index),
    }))
  }

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Tessera</h1>
          <span className="subtitle">설정</span>
        </div>
        <button className="btn-tg-test" onClick={onBack}>돌아가기</button>
      </header>

      <main className="app-main">
        {/* KTX 계정 */}
        <div className="card">
          <div className="settings-header">
            <h3 className="section-title" style={{ marginBottom: 0 }}>KTX 계정 (Korail)</h3>
            {ktxLoggedIn && <span className="ktx-status-badge">등록됨: {ktxCurrentId}</span>}
          </div>
          {ktxLoggedIn ? (
            <div className="settings-form">
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                KTX 계정이 등록되어 있습니다. KTX 예매가 가능합니다.
              </p>
              <button className="btn-test" onClick={handleKtxLogout}>
                KTX 계정 해제
              </button>
            </div>
          ) : (
            <div className="settings-form">
              <div className="form-group">
                <label>코레일 ID (회원번호 / 이메일 / 휴대폰)</label>
                <input
                  type="text"
                  value={ktxId}
                  onChange={(e) => setKtxId(e.target.value)}
                  placeholder="회원번호, 이메일 또는 휴대폰번호"
                  autoComplete="off"
                />
              </div>
              <div className="form-group">
                <label>비밀번호</label>
                <input
                  type="password"
                  value={ktxPassword}
                  onChange={(e) => setKtxPassword(e.target.value)}
                  placeholder="코레일 비밀번호"
                />
              </div>
              <button
                className="btn-test"
                onClick={handleKtxLogin}
                disabled={ktxSaving || !ktxId || !ktxPassword}
              >
                {ktxSaving ? '검증 중...' : 'KTX 계정 등록'}
              </button>
            </div>
          )}
        </div>

        {/* Polling settings */}
        <div className="card">
          <h3 className="section-title">예매 설정</h3>
          <div className="settings-form">
            <div className="form-row">
              <div className="form-group">
                <label>상태 리포트 주기 (초)</label>
                <input
                  type="number"
                  min={10}
                  value={settings.report_interval_seconds}
                  onChange={(e) => setSettings({ ...settings, report_interval_seconds: Number(e.target.value) })}
                  style={{ maxWidth: '100%' }}
                />
              </div>
              <div className="form-group">
                <label>최대 시도 횟수 (0=무제한)</label>
                <input
                  type="number"
                  min={0}
                  value={settings.max_attempts}
                  onChange={(e) => setSettings({ ...settings, max_attempts: Number(e.target.value) })}
                  style={{ maxWidth: '100%' }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Telegram */}
        <div className="card">
          <div className="settings-header">
            <h3 className="section-title" style={{ marginBottom: 0 }}>Telegram</h3>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={settings.telegram_enabled}
                onChange={(e) => setSettings({ ...settings, telegram_enabled: e.target.checked })}
              />
              <span>{settings.telegram_enabled ? '활성' : '비활성'}</span>
            </label>
          </div>
          {settings.telegram_enabled && (
            <div className="settings-form">
              <div className="form-group">
                <label>Bot Token</label>
                <input
                  type="text"
                  value={settings.telegram_bot_token}
                  onChange={(e) => setSettings({ ...settings, telegram_bot_token: e.target.value })}
                  placeholder="123456:ABC-DEF..."
                />
              </div>
              <div className="form-group">
                <label>Chat ID</label>
                <input
                  type="text"
                  value={settings.telegram_chat_id}
                  onChange={(e) => setSettings({ ...settings, telegram_chat_id: e.target.value })}
                  placeholder="123456789"
                />
              </div>
              <button
                className="btn-test"
                onClick={handleTestTelegram}
                disabled={testingTg || !settings.telegram_bot_token || !settings.telegram_chat_id}
              >
                {testingTg ? '전송 중...' : '테스트 전송'}
              </button>
            </div>
          )}
        </div>

        {/* iMessage - macOS only */}
        {isMac && (
          <div className="card">
            <div className="settings-header">
              <h3 className="section-title" style={{ marginBottom: 0 }}>iMessage</h3>
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={settings.imessage_enabled}
                  onChange={(e) => setSettings({ ...settings, imessage_enabled: e.target.checked })}
                />
                <span>{settings.imessage_enabled ? '활성' : '비활성'}</span>
              </label>
            </div>
            {settings.imessage_enabled && (
              <div className="settings-form">
                <label className="form-label-sm">수신자 (최대 5명)</label>
                {settings.imessage_recipients.map((r, i) => (
                  <div key={i} className="recipient-row">
                    <input
                      type="text"
                      value={r}
                      onChange={(e) => setRecipient(i, e.target.value)}
                      placeholder="전화번호 또는 이메일"
                    />
                    <button className="btn-remove" onClick={() => removeRecipient(i)}>×</button>
                  </div>
                ))}
                {settings.imessage_recipients.length < 5 && (
                  <button className="btn-add" onClick={addRecipient}>+ 수신자 추가</button>
                )}
                <button
                  className="btn-test"
                  onClick={handleTestImessage}
                  disabled={testingIm || settings.imessage_recipients.filter(Boolean).length === 0}
                >
                  {testingIm ? '전송 중...' : '테스트 전송'}
                </button>
              </div>
            )}
          </div>
        )}

        {message && <p className={message.includes('실패') || message.includes('오류') ? 'error' : 'success-msg'}>{message}</p>}

        <button className="btn-primary save-btn" onClick={handleSave} disabled={saving}>
          {saving ? '저장 중...' : '설정 저장'}
        </button>
      </main>
    </div>
  )
}
