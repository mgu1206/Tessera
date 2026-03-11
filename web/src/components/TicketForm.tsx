import { useState, FormEvent } from 'react'
import { TicketCreateRequest, SeatType } from '../types'

const STATIONS = [
  '수서', '동탄', '평택지제', '천안아산', '오송', '대전', '김천(구미)',
  '동대구', '서대구', '신경주', '경주', '울산(통도사)', '부산',
  '공주', '익산', '전주', '정읍', '광주송정', '나주', '목포',
  '여수EXPO', '여천', '순천', '곡성', '구례구', '남원', '밀양',
  '창원중앙', '창원', '마산', '진영', '진주', '포항',
]

interface Props {
  onSubmit: (data: TicketCreateRequest) => Promise<void>
}

export function TicketForm({ onSubmit }: Props) {
  const today = new Date().toISOString().slice(0, 10)
  const [dep, setDep] = useState('수서')
  const [arr, setArr] = useState('부산')
  const [date, setDate] = useState(today)
  const [time, setTime] = useState('00:00')
  const [timeLimit, setTimeLimit] = useState('23:59')
  const [seatType, setSeatType] = useState<SeatType>('GENERAL_FIRST')
  const [adult, setAdult] = useState(1)
  const [child, setChild] = useState(0)
  const [senior, setSenior] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await onSubmit({
        dep,
        arr,
        date: date.replace(/-/g, ''),
        time: time.replace(':', '') + '00',
        time_limit: timeLimit.replace(':', '') + '00',
        seat_type: seatType,
        passengers: { adult, child, senior },
      })
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '오류가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="card">
      <h2 className="section-title">예약 요청</h2>

      <div className="form-row">
        <div className="form-group">
          <label>출발역</label>
          <select value={dep} onChange={(e) => setDep(e.target.value)}>
            {STATIONS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
        <div className="form-arrow">→</div>
        <div className="form-group">
          <label>도착역</label>
          <select value={arr} onChange={(e) => setArr(e.target.value)}>
            {STATIONS.map((s) => <option key={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>날짜</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>시간 범위</label>
          <div className="time-range">
            <input type="time" value={time} onChange={(e) => setTime(e.target.value)} required />
            <span>~</span>
            <input type="time" value={timeLimit} onChange={(e) => setTimeLimit(e.target.value)} required />
          </div>
        </div>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label>좌석</label>
          <select value={seatType} onChange={(e) => setSeatType(e.target.value as SeatType)}>
            <option value="GENERAL_FIRST">일반실 우선</option>
            <option value="GENERAL_ONLY">일반실만</option>
            <option value="SPECIAL_FIRST">특실 우선</option>
            <option value="SPECIAL_ONLY">특실만</option>
          </select>
        </div>
        <div className="form-group">
          <label>성인</label>
          <input type="number" min={0} max={9} value={adult} onChange={(e) => setAdult(+e.target.value)} />
        </div>
        <div className="form-group">
          <label>어린이</label>
          <input type="number" min={0} max={9} value={child} onChange={(e) => setChild(+e.target.value)} />
        </div>
        <div className="form-group">
          <label>경로</label>
          <input type="number" min={0} max={9} value={senior} onChange={(e) => setSenior(+e.target.value)} />
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      <button type="submit" className="btn-primary" disabled={loading}>
        {loading ? '요청 중...' : '예약 시도 시작'}
      </button>
    </form>
  )
}
