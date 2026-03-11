import { Ticket } from '../types'
import { cancelTicket } from '../api/tickets'

const STATUS_LABEL: Record<string, string> = {
  PENDING: '대기',
  POLLING: '조회 중',
  SUCCESS: '예매 완료',
  FAILED: '실패',
  CANCELLED: '취소됨',
}

const STATUS_CLASS: Record<string, string> = {
  PENDING: 'status-pending',
  POLLING: 'status-polling',
  SUCCESS: 'status-success',
  FAILED: 'status-failed',
  CANCELLED: 'status-cancelled',
}

function elapsed(createdAt: string): string {
  const diff = Math.floor((Date.now() - new Date(createdAt).getTime()) / 1000)
  if (diff < 60) return `${diff}초`
  if (diff < 3600) return `${Math.floor(diff / 60)}분`
  return `${Math.floor(diff / 3600)}시간 ${Math.floor((diff % 3600) / 60)}분`
}

function formatDate(d: string): string {
  return `${d.slice(0, 4)}-${d.slice(4, 6)}-${d.slice(6, 8)}`
}

function formatTime(t: string): string {
  return `${t.slice(0, 2)}:${t.slice(2, 4)}`
}

interface Props {
  ticket: Ticket
  onCancelled: (id: string) => void
  onDeleted: (id: string) => void
}

export function TicketCard({ ticket, onCancelled, onDeleted }: Props) {
  async function handleCancel() {
    if (!confirm(`티켓 #${ticket.ticket_id}를 취소하시겠습니까?`)) return
    try {
      await cancelTicket(ticket.ticket_id)
      onCancelled(ticket.ticket_id)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : '취소 실패')
    }
  }

  async function handleDelete() {
    if (!confirm(`티켓 #${ticket.ticket_id}를 삭제하시겠습니까?`)) return
    try {
      await cancelTicket(ticket.ticket_id)
      onDeleted(ticket.ticket_id)
    } catch (e: unknown) {
      alert(e instanceof Error ? e.message : '삭제 실패')
    }
  }

  const info = ticket.reservation_info
  const canCancel = ticket.status === 'POLLING' || ticket.status === 'PENDING'
  const canDelete = ticket.status === 'SUCCESS' || ticket.status === 'FAILED' || ticket.status === 'CANCELLED'

  return (
    <div className={`ticket-card ${ticket.status === 'SUCCESS' ? 'ticket-success' : ''}`}>
      <div className="ticket-header">
        <span className="ticket-id">#{ticket.ticket_id}</span>
        <span className={`status-badge ${STATUS_CLASS[ticket.status]}`}>
          {STATUS_LABEL[ticket.status]}
        </span>
        {canCancel && (
          <button className="btn-cancel" onClick={handleCancel}>취소</button>
        )}
        {canDelete && (
          <button className="btn-cancel" onClick={handleDelete}>삭제</button>
        )}
      </div>

      <div className="ticket-route">
        <span className="station">{ticket.dep}</span>
        <span className="arrow">→</span>
        <span className="station">{ticket.arr}</span>
        <span className="date">{formatDate(ticket.date)}</span>
        <span className="time-range">
          {formatTime(ticket.time)}
          {ticket.time_limit && ` ~ ${formatTime(ticket.time_limit)}`}
        </span>
      </div>

      <div className="ticket-meta">
        <span>{ticket.seat_type === 'GENERAL_FIRST' || ticket.seat_type === 'GENERAL_ONLY' ? '일반실' : '특실'}</span>
        <span>성인 {ticket.passengers.adult}명{ticket.passengers.child > 0 && ` · 어린이 ${ticket.passengers.child}명`}{ticket.passengers.senior > 0 && ` · 경로 ${ticket.passengers.senior}명`}</span>
      </div>

      {ticket.status === 'POLLING' && (
        <div className="ticket-progress">
          <span>시도 {ticket.attempt_count.toLocaleString()}회</span>
          <span>경과 {elapsed(ticket.created_at)}</span>
          {ticket.last_searched_at && (
            <span>마지막 조회 {new Date(ticket.last_searched_at).toLocaleTimeString('ko-KR')}</span>
          )}
        </div>
      )}

      {ticket.status === 'POLLING' && ticket.last_search_results && ticket.last_search_results.length > 0 && (
        <div className="train-results">
          <table className="train-table">
            <thead>
              <tr>
                <th>열차</th>
                <th>출발</th>
                <th>도착</th>
                <th>일반실</th>
                <th>특실</th>
              </tr>
            </thead>
            <tbody>
              {ticket.last_search_results.map((t) => (
                <tr key={t.train_number}>
                  <td className="train-name">{t.train_name} {t.train_number}</td>
                  <td>{formatTime(t.dep_time)}</td>
                  <td>{formatTime(t.arr_time)}</td>
                  <td className={t.general_available ? 'seat-available' : 'seat-unavailable'}>
                    {t.general_seat}
                  </td>
                  <td className={t.special_available ? 'seat-available' : 'seat-unavailable'}>
                    {t.special_seat}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {info && (
        <div className="ticket-result">
          <div className="result-row">
            <span>{info.train_name} {info.train_number}</span>
            <span>{formatTime(info.dep_time)} → {formatTime(info.arr_time)}</span>
          </div>
          <div className="result-row">
            <span className="price">{info.total_cost.toLocaleString()}원</span>
            <span className="deadline">결제기한 {info.payment_date} {formatTime(info.payment_time)}</span>
          </div>
        </div>
      )}
    </div>
  )
}
