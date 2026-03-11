from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from tgbot.api.client import create_ticket

SEAT_TYPE_LABELS = {
    "GENERAL_FIRST": "일반실 우선",
    "GENERAL_ONLY": "일반실만",
    "SPECIAL_FIRST": "특실 우선",
    "SPECIAL_ONLY": "특실만",
}

SEAT_TYPE_ALIASES = {
    "일반우선": "GENERAL_FIRST",
    "일반실우선": "GENERAL_FIRST",
    "일반만": "GENERAL_ONLY",
    "일반실만": "GENERAL_ONLY",
    "특실우선": "SPECIAL_FIRST",
    "특실만": "SPECIAL_ONLY",
}

USAGE_TEXT = (
    "사용법: /book 출발역 도착역 날짜 시작시간 [종료시간] [좌석] [인원]\n"
    "\n"
    "형식:\n"
    "  날짜: YYYYMMDD (예: 20260315)\n"
    "  시간: HHMM (예: 0700, 1830)\n"
    "  좌석: 일반우선(기본), 일반만, 특실우선, 특실만\n"
    "  인원: 성인N 어린이N 경로N (기본: 성인1)\n"
    "\n"
    "예시:\n"
    "  /book 수서 부산 20260315 0700\n"
    "  /book 동대구 동탄 20260315 1700 2000\n"
    "  /book 수서 부산 20260315 0700 1200 특실우선 성인2\n"
    "  /book 수서 부산 20260315 0700 1200 일반만 성인1 어린이2"
)


def _parse_args(args: list[str]) -> dict | None:
    """Parse structured booking arguments."""
    if len(args) < 4:
        return None

    dep = args[0]
    arr = args[1]
    raw_date = args[2]
    raw_time = args[3]

    # Validate date format (YYYYMMDD)
    if len(raw_date) != 8 or not raw_date.isdigit():
        return None

    # Validate time format (HHMM)
    if len(raw_time) != 4 or not raw_time.isdigit():
        return None

    time_ = raw_time + "00"  # HHMM -> HHMMss

    # Parse remaining optional args
    time_limit = None
    seat_type = "GENERAL_FIRST"
    passengers = {"adult": 1, "child": 0, "senior": 0}

    i = 4
    while i < len(args):
        token = args[i]

        # Check if it's a time limit (4-digit number)
        if len(token) == 4 and token.isdigit() and time_limit is None:
            time_limit = token + "00"
            i += 1
            continue

        # Check if it's a seat type alias
        if token in SEAT_TYPE_ALIASES:
            seat_type = SEAT_TYPE_ALIASES[token]
            i += 1
            continue

        # Check if it's a passenger spec: 성인N, 어린이N, 경로N
        if token.startswith("성인") and token[2:].isdigit():
            passengers["adult"] = int(token[2:])
            i += 1
            continue
        if token.startswith("어린이") and token[3:].isdigit():
            passengers["child"] = int(token[3:])
            i += 1
            continue
        if token.startswith("경로") and token[2:].isdigit():
            passengers["senior"] = int(token[2:])
            i += 1
            continue

        # Unknown token, skip
        i += 1

    return {
        "dep": dep,
        "arr": arr,
        "date": raw_date,
        "time": time_,
        "time_limit": time_limit,
        "seat_type": seat_type,
        "passengers": passengers,
    }


def _format_confirmation(params: dict) -> str:
    dep = params["dep"]
    arr = params["arr"]
    raw_date = params["date"]
    date_str = f"{raw_date[:4]}-{raw_date[4:6]}-{raw_date[6:8]}"

    raw_time = params.get("time", "000000")
    time_str = f"{raw_time[:2]}:{raw_time[2:4]}"

    time_limit = params.get("time_limit")
    if time_limit:
        limit_str = f"{time_limit[:2]}:{time_limit[2:4]}"
        time_line = f"시간: {time_str} ~ {limit_str}"
    else:
        time_line = f"시간: {time_str} 이후"

    seat_label = SEAT_TYPE_LABELS.get(
        params.get("seat_type", "GENERAL_FIRST"), "일반실 우선"
    )

    passengers = params.get("passengers", {"adult": 1, "child": 0, "senior": 0})
    pax_parts = []
    if passengers.get("adult", 0) > 0:
        pax_parts.append(f"성인 {passengers['adult']}명")
    if passengers.get("child", 0) > 0:
        pax_parts.append(f"어린이 {passengers['child']}명")
    if passengers.get("senior", 0) > 0:
        pax_parts.append(f"경로 {passengers['senior']}명")
    pax_str = ", ".join(pax_parts) if pax_parts else "성인 1명"

    return (
        "아래 내용으로 예매를 시도할까요?\n"
        "\n"
        f"출발: {dep} → {arr}\n"
        f"날짜: {date_str}\n"
        f"{time_line}\n"
        f"좌석: {seat_label}\n"
        f"승객: {pax_str}"
    )


async def booking_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    args = context.args or []

    if not args:
        await update.message.reply_text(USAGE_TEXT)
        return

    params = _parse_args(args)

    if params is None:
        await update.message.reply_text(
            "입력 형식이 올바르지 않습니다.\n\n" + USAGE_TEXT
        )
        return

    context.user_data["pending_booking"] = params

    confirmation = _format_confirmation(params)
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("예약 시작", callback_data="booking_confirm"),
                InlineKeyboardButton("취소", callback_data="booking_cancel"),
            ]
        ]
    )

    await update.message.reply_text(confirmation, reply_markup=keyboard)


async def _booking_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == "booking_confirm":
        params = context.user_data.pop("pending_booking", None)
        if params is None:
            await query.edit_message_text("만료된 요청입니다. 다시 시도해주세요.")
            return

        try:
            ticket = await create_ticket(params)
            ticket_id = ticket.get("ticket_id", "?")
            await query.edit_message_text(
                f"[티켓 #{ticket_id}] 예매 요청이 접수되었습니다."
            )
        except Exception as e:
            await query.edit_message_text(f"예매 요청 실패: {e}")

    elif query.data == "booking_cancel":
        context.user_data.pop("pending_booking", None)
        await query.edit_message_text("예매 요청이 취소되었습니다.")


def register_handlers(application: Application) -> None:
    application.add_handler(CommandHandler("book", booking_command))
    application.add_handler(
        CallbackQueryHandler(_booking_callback, pattern="^booking_")
    )
