import { useEffect, useState } from 'react'
import {
  AppSettings,
  getSettings,
  updateSettings,
  testTelegram,
  testImessage,
  getSystemInfo,
} from '../api/settings'
import { srtLogin, srtClear, ktxLogin, ktxLogout, getAuthStatus } from '../api/auth'

interface Props {
  onBack?: () => void        // undefined이면 첫 실행 모드
  onAccountChange?: (srtLoggedIn: boolean, srtId: string | null, ktxLoggedIn: boolean, ktxId: string | null) => void
}

export function SettingsPage({ onBack, onAccountChange }: Props) {
  const isFirstRun = !onBack

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

  // SRT 상태
  const [srtLoggedIn, setSrtLoggedIn] = useState(false)
  const [srtCurrentId, setSrtCurrentId] = useState<string | null>(null)
  const [srtId, setSrtId] = useState('')
  const [srtPassword, setSrtPassword] = useState('')
  const [srtSaving, setSrtSaving] = useState(false)

  // KTX 상태
  const [ktxLoggedIn, setKtxLoggedIn] = useState(false)
  const [ktxCurrentId, setKtxCurrentId] = useState<string | null>(null)
  const [ktxId, setKtxId] = useState('')
  const [ktxPassword, setKtxPassword] = useState('')
  const [ktxSaving, setKtxSaving] = useState(false)

  const anyLoggedIn = srtLoggedIn || ktxLoggedIn

  useEffect(() => {
    getSettings().then(setSettings).catch(() => {})
    getSystemInfo().then((info) => setIsMac(info.platform === 'Darwin')).catch(() => {})
    getAuthStatus().then((s) => {
      setSrtLoggedIn(s.logged_in)
      setSrtCurrentId(s.srt_id)
      setKtxLoggedIn(s.ktx_logged_in)
      setKtxCurrentId(s.ktx_id)
    }).catch(() => {})
  }, [])

  function notifyChange(sl: boolean, sid: string | null, kl: boolean, kid: string | null) {
    onAccountChange?.(sl, sid, kl, kid)
  }

  async function handleSrtLogin() {
    if (!srtId || !srtPassword) { setMessage('SRT ID와 비밀번호를 입력하세요.'); return }
    setSrtSaving(true)
    setMessage('')
    try {
      await srtLogin(srtId, srtPassword)
      setSrtLoggedIn(true)
      setSrtCurrentId(srtId)
      setSrtPassword('')
      setMessage('SRT 계정 등록 완료')
      notifyChange(true, srtId, ktxLoggedIn, ktxCurrentId)
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : 'SRT 로그인 실패')
    } finally {
      setSrtSaving(false)
    }
  }

  async function handleSrtClear() {
    try {
      await srtClear()
      setSrtLoggedIn(false)
      setSrtCurrentId(null)
      setSrtId('')
      setSrtPassword('')
      setMessage('SRT 계정 해제 완료')
      notifyChange(false, null, ktxLoggedIn, ktxCurrentId)
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : 'SRT 계정 해제 실패')
    }
  }

  async function handleKtxLogin() {
    if (!ktxId || !ktxPassword) { setMessage('KTX ID와 비밀번호를 입력하세요.'); return }
    setKtxSaving(true)
    setMessage('')
    try {
      await ktxLogin(ktxId, ktxPassword)
      setKtxLoggedIn(true)
      setKtxCurrentId(ktxId)
      setKtxPassword('')
      setMessage('KTX 계정 등록 완료')
      notifyChange(srtLoggedIn, srtCurrentId, true, ktxId)
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : 'KTX 로그인 실패')
    } finally {
      setKtxSaving(false)
    }
  }

  async function handleKtxClear() {
    try {
      await ktxLogout()
      setKtxLoggedIn(false)
      setKtxCurrentId(null)
      setKtxId('')
      setKtxPassword('')
      setMessage('KTX 계정 해제 완료')
      notifyChange(srtLoggedIn, srtCurrentId, false, null)
    } catch (err: unknown) {
      setMessage(err instanceof Error ? err.message : 'KTX 계정 해제 실패')
    }
  }

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

  function setRecipient(index: number, value: string) {
    setSettings((prev) => {
      const recipients = [...prev.imessage_recipients]
      recipients[index] = value
      return { ...prev, imessage_recipients: recipients }
    })
  }

  function addRecipient() {
    if (settings.imessage_recipients.length >= 5) return
    setSettings((prev) => ({ ...prev, imessage_recipients: [...prev.imessage_recipients, ''] }))
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
          <span className="subtitle">{isFirstRun ? '계정 설정' : '설정'}</span>
        </div>
        {onBack && (
          <button className="btn-tg-test" onClick={onBack}>돌아가기</button>
        )}
      </header>

      <main className="app-main">
        {isFirstRun && (
          <div className="card" style={{ borderColor: 'var(--accent)', background: '#111827' }}>
            <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
              SRT 또는 KTX 계정을 하나 이상 등록하면 자동 예매를 시작할 수 있습니다.
            </p>
          </div>
        )}

        {/* SRT 계정 */}
        <div className="card">
          <div className="settings-header">
            <h3 className="section-title" style={{ marginBottom: 0 }}>SRT 계정</h3>
            {srtLoggedIn && <span className="ktx-status-badge" style={{ background: '#1e3a6e', color: '#6faaff' }}>등록됨: {srtCurrentId}</span>}
          </div>
          {srtLoggedIn ? (
            <div className="settings-form">
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                SRT 계정이 등록되어 있습니다. SRT 자동 예매가 가능합니다.
              </p>
              <div className="settings-account-actions">
                <button className="btn-test" onClick={() => setSrtLoggedIn(false)}>
                  계정 변경
                </button>
                <button className="btn-test" style={{ color: 'var(--danger)', borderColor: 'var(--border)' }} onClick={handleSrtClear}>
                  계정 해제
                </button>
              </div>
            </div>
          ) : (
            <div className="settings-form">
              {!srtLoggedIn && srtCurrentId === null && (
                <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>SRT 회원번호 또는 이메일로 로그인하세요.</p>
              )}
              <div className="form-group">
                <label>SRT 회원번호 / 이메일</label>
                <input
                  type="text"
                  value={srtId}
                  onChange={(e) => setSrtId(e.target.value)}
                  placeholder="회원번호 또는 이메일"
                  autoComplete="off"
                />
              </div>
              <div className="form-group">
                <label>비밀번호</label>
                <input
                  type="password"
                  value={srtPassword}
                  onChange={(e) => setSrtPassword(e.target.value)}
                  placeholder="SRT 비밀번호"
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSrtLogin() }}
                />
              </div>
              <div className="settings-account-actions">
                <button
                  className="btn-test"
                  onClick={handleSrtLogin}
                  disabled={srtSaving || !srtId || !srtPassword}
                >
                  {srtSaving ? '검증 중...' : 'SRT 계정 등록'}
                </button>
                {srtCurrentId !== null && (
                  <button className="btn-test" onClick={() => { setSrtLoggedIn(true) }}>취소</button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* KTX 계정 */}
        <div className="card">
          <div className="settings-header">
            <h3 className="section-title" style={{ marginBottom: 0 }}>KTX 계정 (Korail)</h3>
            {ktxLoggedIn && <span className="ktx-status-badge">등록됨: {ktxCurrentId}</span>}
          </div>
          {ktxLoggedIn ? (
            <div className="settings-form">
              <p style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                KTX 계정이 등록되어 있습니다. KTX 자동 예매가 가능합니다.
              </p>
              <div className="settings-account-actions">
                <button className="btn-test" onClick={() => setKtxLoggedIn(false)}>
                  계정 변경
                </button>
                <button className="btn-test" style={{ color: 'var(--danger)', borderColor: 'var(--border)' }} onClick={handleKtxClear}>
                  계정 해제
                </button>
              </div>
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
                  onKeyDown={(e) => { if (e.key === 'Enter') handleKtxLogin() }}
                />
              </div>
              <div className="settings-account-actions">
                <button
                  className="btn-test"
                  onClick={handleKtxLogin}
                  disabled={ktxSaving || !ktxId || !ktxPassword}
                >
                  {ktxSaving ? '검증 중...' : 'KTX 계정 등록'}
                </button>
                {ktxCurrentId !== null && (
                  <button className="btn-test" onClick={() => { setKtxLoggedIn(true) }}>취소</button>
                )}
              </div>
            </div>
          )}
        </div>

        {/* 첫 실행 모드: 시작 버튼 */}
        {isFirstRun && (
          <button
            className="btn-primary"
            style={{ width: '100%', padding: '12px', fontSize: 15 }}
            disabled={!anyLoggedIn}
            onClick={() => onAccountChange?.(srtLoggedIn, srtCurrentId, ktxLoggedIn, ktxCurrentId)}
          >
            {anyLoggedIn ? '예매 시작하기' : '계정을 하나 이상 등록하세요'}
          </button>
        )}

        {/* 일반 설정 모드에서만 표시 */}
        {!isFirstRun && (
          <>
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
          </>
        )}

        {isFirstRun && message && (
          <p className={message.includes('실패') || message.includes('오류') ? 'error' : 'success-msg'}>{message}</p>
        )}
      </main>
    </div>
  )
}
