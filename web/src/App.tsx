import { useEffect, useState } from 'react'
import { Ticket, TicketCreateRequest } from './types'
import { listTickets, createTicket, patchTicket } from './api/tickets'
import { getAuthStatus, srtLogout } from './api/auth'
import { subscribeEvents } from './api/events'
import { TicketForm } from './components/TicketForm'
import { TicketCard } from './components/TicketCard'
import { SettingsPage } from './components/SettingsPage'

type Page = 'main' | 'settings'

export function App() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null)
  const [srtId, setSrtId] = useState<string | null>(null)
  const [ktxLoggedIn, setKtxLoggedIn] = useState(false)
  const [ktxId, setKtxId] = useState<string | null>(null)
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loadError, setLoadError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const [page, setPage] = useState<Page>('main')

  // 그룹화 관련 상태
  const [selectionMode, setSelectionMode] = useState(false)
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())
  const [groupInputVisible, setGroupInputVisible] = useState(false)
  const [groupName, setGroupName] = useState('')
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set())

  useEffect(() => {
    getAuthStatus()
      .then((s) => {
        setLoggedIn(s.logged_in || s.ktx_logged_in)
        setSrtId(s.srt_id)
        setKtxLoggedIn(s.ktx_logged_in)
        setKtxId(s.ktx_id)
      })
      .catch(() => setLoggedIn(false))
  }, [])

  useEffect(() => {
    if (!loggedIn) return

    listTickets()
      .then(setTickets)
      .catch((e) => setLoadError(e.message))

    const unsub = subscribeEvents((type, data) => {
      if (type === 'ticket.created') {
        setTickets((prev) => {
          if (prev.some((t) => t.ticket_id === (data as Ticket).ticket_id)) return prev
          return [data as Ticket, ...prev]
        })
      } else if (type === 'ticket.cancelled') {
        setTickets((prev) =>
          prev.map((t) =>
            t.ticket_id === (data as unknown as { ticket_id: string }).ticket_id
              ? { ...t, status: 'CANCELLED' }
              : t
          )
        )
      } else if (type === 'ticket.deleted') {
        setTickets((prev) =>
          prev.filter((t) => t.ticket_id !== (data as unknown as { ticket_id: string }).ticket_id)
        )
      } else {
        setTickets((prev) =>
          prev.map((t) => (t.ticket_id === data.ticket_id ? { ...t, ...data } : t))
        )
      }
    })

    return unsub
  }, [loggedIn])

  function handleAccountChange(srtIn: boolean, sid: string | null, ktxIn: boolean, kid: string | null) {
    setSrtId(sid)
    setKtxLoggedIn(ktxIn)
    setKtxId(kid)
    if (srtIn || ktxIn) {
      setLoggedIn(true)
      setTickets([])
      setLoadError('')
    } else {
      setLoggedIn(false)
    }
  }

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await srtLogout()
    } catch { /* ignore */ }
    setLoggedIn(false)
    setSrtId(null)
    setTickets([])
    setLoggingOut(false)
  }

  async function handleCreate(req: TicketCreateRequest) {
    await createTicket(req)
  }

  function handleCancelled(id: string) {
    setTickets((prev) =>
      prev.map((t) => (t.ticket_id === id ? { ...t, status: 'CANCELLED' } : t))
    )
  }

  function handleDeleted(id: string) {
    setTickets((prev) => prev.filter((t) => t.ticket_id !== id))
  }

  function handleUpdated(updated: Ticket) {
    setTickets((prev) => prev.map((t) => (t.ticket_id === updated.ticket_id ? updated : t)))
  }

  function toggleGroup(gid: string) {
    setCollapsedGroups((prev) => {
      const next = new Set(prev)
      if (next.has(gid)) next.delete(gid)
      else next.add(gid)
      return next
    })
  }

  function toggleSelectionMode() {
    setSelectionMode((v) => !v)
    setSelectedIds(new Set())
    setGroupInputVisible(false)
    setGroupName('')
  }

  function toggleSelectTicket(id: string) {
    setSelectedIds((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function handleCreateGroup() {
    const name = groupName.trim()
    if (!name) { alert('그룹 이름을 입력하세요.'); return }
    if (selectedIds.size === 0) { alert('티켓을 선택하세요.'); return }

    try {
      await Promise.all(
        Array.from(selectedIds).map((id) => patchTicket(id, { group_id: name }))
      )
      setTickets((prev) =>
        prev.map((t) => selectedIds.has(t.ticket_id) ? { ...t, group_id: name } : t)
      )
      setSelectionMode(false)
      setSelectedIds(new Set())
      setGroupInputVisible(false)
      setGroupName('')
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : '그룹 생성 실패')
    }
  }

  async function handleUngroup(ticketId: string) {
    try {
      const updated = await patchTicket(ticketId, { group_id: '' })
      handleUpdated(updated)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : '그룹 해제 실패')
    }
  }

  if (loggedIn === null) {
    return <div className="app"><p className="empty">로딩 중...</p></div>
  }

  if (!loggedIn) {
    return (
      <SettingsPage
        onAccountChange={handleAccountChange}
      />
    )
  }

  if (page === 'settings') {
    return (
      <SettingsPage
        onBack={() => setPage('main')}
        onAccountChange={(sl, sid, kl, kid) => {
          setSrtId(sid)
          setKtxLoggedIn(kl)
          setKtxId(kid)
          if (!sl && !kl) setLoggedIn(false)
        }}
      />
    )
  }

  const active = tickets.filter((t) => t.status === 'POLLING' || t.status === 'PENDING')
  const done = tickets.filter((t) => t.status !== 'POLLING' && t.status !== 'PENDING')

  // 그룹화된 티켓 분리
  const groupedTickets = done.filter((t) => t.group_id)
  const ungroupedDone = done.filter((t) => !t.group_id)

  // 그룹 ID 목록
  const groupIds = Array.from(new Set(groupedTickets.map((t) => t.group_id!)))

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Tessera</h1>
          <span className="subtitle">
            {srtId && `SRT: ${srtId}`}
            {srtId && ktxLoggedIn && ' · '}
            {ktxLoggedIn && <span className="ktx-active-badge">KTX: {ktxId}</span>}
          </span>
        </div>
        <div className="header-actions">
          <button className="btn-tg-test" onClick={() => setPage('settings')}>설정</button>
          <button
            className={`btn-tg-test${selectionMode ? ' btn-select-active' : ''}`}
            onClick={toggleSelectionMode}
          >
            {selectionMode ? '선택 취소' : '그룹 선택'}
          </button>
          <button className="btn-logout" onClick={handleLogout} disabled={loggingOut}>
            {loggingOut ? '로그아웃 중...' : '로그아웃'}
          </button>
        </div>
      </header>

      <main className="app-main">
        <TicketForm onSubmit={handleCreate} ktxLoggedIn={ktxLoggedIn} />

        {loadError && <p className="error">{loadError}</p>}

        {/* 그룹 생성 UI */}
        {selectionMode && (
          <div className="group-create-bar card">
            <span className="group-create-hint">
              {selectedIds.size === 0 ? '아래 티켓을 클릭해서 선택하세요' : `${selectedIds.size}개 선택됨`}
            </span>
            {selectedIds.size > 0 && !groupInputVisible && (
              <button className="btn-primary" style={{ marginTop: 0, padding: '6px 16px' }} onClick={() => setGroupInputVisible(true)}>
                그룹으로 묶기
              </button>
            )}
            {groupInputVisible && (
              <div className="group-name-input">
                <input
                  type="text"
                  placeholder="그룹 이름 입력 (예: 가족여행 4월)"
                  value={groupName}
                  onChange={(e) => setGroupName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleCreateGroup() }}
                  autoFocus
                />
                <button className="btn-primary" style={{ marginTop: 0, flexShrink: 0 }} onClick={handleCreateGroup}>
                  확인
                </button>
                <button className="btn-tg-test" onClick={() => setGroupInputVisible(false)}>
                  취소
                </button>
              </div>
            )}
          </div>
        )}

        {/* 진행 중 */}
        {active.length > 0 && (
          <section>
            <h2 className="section-title">진행 중 ({active.length})</h2>
            {active.map((t) => (
              <TicketCard
                key={t.ticket_id}
                ticket={t}
                onCancelled={handleCancelled}
                onDeleted={handleDeleted}
                onUpdated={handleUpdated}
                selectable={selectionMode}
                selected={selectedIds.has(t.ticket_id)}
                onSelectToggle={toggleSelectTicket}
              />
            ))}
          </section>
        )}

        {/* 그룹별 완료 티켓 */}
        {groupIds.map((gid) => {
          const gTickets = groupedTickets.filter((t) => t.group_id === gid)
          const completedCount = gTickets.filter((t) => t.manually_completed).length
          return (
            <section key={gid} className="group-section">
              <div className="group-header">
                <h2 className="section-title" style={{ marginBottom: 0 }}>
                  {gid}
                  <span className="group-count"> ({completedCount}/{gTickets.length} 완료)</span>
                </h2>
                <button className="btn-expand-trains" onClick={() => toggleGroup(gid)}>
                  {collapsedGroups.has(gid) ? '▼' : '▲'}
                </button>
              </div>
              {!collapsedGroups.has(gid) && gTickets.map((t) => (
                <TicketCard
                  key={t.ticket_id}
                  ticket={t}
                  onCancelled={handleCancelled}
                  onDeleted={handleDeleted}
                  onUpdated={handleUpdated}
                  selectable={selectionMode}
                  selected={selectedIds.has(t.ticket_id)}
                  onSelectToggle={toggleSelectTicket}
                />
              ))}
            </section>
          )
        })}

        {/* 그룹 없는 완료 티켓 */}
        {ungroupedDone.length > 0 && (
          <section>
            <h2 className="section-title">완료</h2>
            {ungroupedDone.map((t) => (
              <TicketCard
                key={t.ticket_id}
                ticket={t}
                onCancelled={handleCancelled}
                onDeleted={handleDeleted}
                onUpdated={handleUpdated}
                selectable={selectionMode}
                selected={selectedIds.has(t.ticket_id)}
                onSelectToggle={toggleSelectTicket}
              />
            ))}
          </section>
        )}

        {tickets.length === 0 && !loadError && (
          <p className="empty">예약 요청이 없습니다. 위 폼에서 시작하세요.</p>
        )}
      </main>
    </div>
  )
}
