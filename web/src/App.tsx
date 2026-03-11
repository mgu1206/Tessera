import { useEffect, useState } from 'react'
import { Ticket, TicketCreateRequest } from './types'
import { listTickets, createTicket } from './api/tickets'
import { getAuthStatus, srtLogout } from './api/auth'
import { subscribeEvents } from './api/events'
import { TicketForm } from './components/TicketForm'
import { TicketCard } from './components/TicketCard'
import { LoginPage } from './components/LoginPage'
import { SettingsPage } from './components/SettingsPage'

type Page = 'main' | 'settings'

export function App() {
  const [loggedIn, setLoggedIn] = useState<boolean | null>(null)
  const [srtId, setSrtId] = useState<string | null>(null)
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loadError, setLoadError] = useState('')
  const [loggingOut, setLoggingOut] = useState(false)
  const [page, setPage] = useState<Page>('main')

  useEffect(() => {
    getAuthStatus()
      .then((s) => {
        setLoggedIn(s.logged_in)
        setSrtId(s.srt_id)
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

  function handleLogin(id: string) {
    setSrtId(id)
    setLoggedIn(true)
    setTickets([])
    setLoadError('')
  }

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await srtLogout()
    } catch {
      // ignore
    }
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

  if (loggedIn === null) {
    return <div className="app"><p className="empty">로딩 중...</p></div>
  }

  if (!loggedIn) {
    return <LoginPage onLogin={handleLogin} />
  }

  if (page === 'settings') {
    return <SettingsPage onBack={() => setPage('main')} />
  }

  const active = tickets.filter((t) => t.status === 'POLLING' || t.status === 'PENDING')
  const done = tickets.filter((t) => t.status !== 'POLLING' && t.status !== 'PENDING')

  return (
    <div className="app">
      <header className="app-header">
        <div>
          <h1>Tessera</h1>
          <span className="subtitle">SRT 자동 예매 — {srtId}</span>
        </div>
        <div className="header-actions">
          <button className="btn-tg-test" onClick={() => setPage('settings')}>설정</button>
          <button className="btn-logout" onClick={handleLogout} disabled={loggingOut}>
            {loggingOut ? '로그아웃 중...' : '로그아웃'}
          </button>
        </div>
      </header>

      <main className="app-main">
        <TicketForm onSubmit={handleCreate} />

        {loadError && <p className="error">{loadError}</p>}

        {active.length > 0 && (
          <section>
            <h2 className="section-title">진행 중 ({active.length})</h2>
            {active.map((t) => (
              <TicketCard key={t.ticket_id} ticket={t} onCancelled={handleCancelled} onDeleted={handleDeleted} />
            ))}
          </section>
        )}

        {done.length > 0 && (
          <section>
            <h2 className="section-title">완료</h2>
            {done.map((t) => (
              <TicketCard key={t.ticket_id} ticket={t} onCancelled={handleCancelled} onDeleted={handleDeleted} />
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
