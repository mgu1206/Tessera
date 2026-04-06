export type TicketStatus = 'PENDING' | 'POLLING' | 'SUCCESS' | 'FAILED' | 'CANCELLED'
export type SeatType = 'GENERAL_FIRST' | 'GENERAL_ONLY' | 'SPECIAL_FIRST' | 'SPECIAL_ONLY'
export type TrainType = 'SRT' | 'KTX'

export interface Passengers {
  adult: number
  child: number
  senior: number
}

export interface ReservationInfo {
  reservation_number: number | string
  total_cost: number
  train_name: string
  train_number: string
  dep_time: string
  arr_time: string
  dep_station_name: string
  arr_station_name: string
  payment_date: string
  payment_time: string
}

export interface TrainResult {
  train_name: string
  train_number: string
  dep_time: string
  arr_time: string
  general_seat: string
  special_seat: string
  general_available: boolean
  special_available: boolean
}

export interface Ticket {
  ticket_id: string
  train_type: TrainType
  dep: string
  arr: string
  date: string
  time: string
  time_limit: string | null
  seat_type: SeatType
  passengers: Passengers
  status: TicketStatus
  attempt_count: number
  created_at: string
  reserved_at: string | null
  reservation_info: ReservationInfo | null
  last_searched_at: string | null
  last_search_results: TrainResult[] | null
  group_id: string | null
  manually_completed: boolean
}

export interface TicketCreateRequest {
  train_type: TrainType
  dep: string
  arr: string
  date: string
  time: string
  time_limit?: string
  seat_type: SeatType
  passengers: Passengers
}

export interface TicketGroup {
  group_id: string
  tickets: Ticket[]
}
