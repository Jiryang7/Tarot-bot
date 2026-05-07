"""
타로 운명 카드 텔레그램 봇
기능 1: 생일 입력 → 양력 카드 + 음력 카드 (자동변환)
기능 2: 이름으로 검색
기능 3: 두 사람 궁합
"""

import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from dotenv import load_dotenv
from tarot import calculate_destiny_card, get_card_info, get_compatibility
from lunar import solar_to_lunar
from sheets import find_person_by_name, save_person

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# ConversationHandler 상태값
# ─────────────────────────────────────────────
(
    MENU,
    BIRTH_INPUT,
    NAME_SEARCH,
    COMPAT_FIRST,
    COMPAT_SECOND_INPUT,
) = range(5)

# ─────────────────────────────────────────────
# 공통 키보드
# ─────────────────────────────────────────────
MAIN_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("🃏 생일로 운명 카드 보기", callback_data="menu_birth")],
    [InlineKeyboardButton("🔍 이름으로 검색",         callback_data="menu_name")],
    [InlineKeyboardButton("💞 두 사람 궁합 보기",     callback_data="menu_compat")],
])


# ─────────────────────────────────────────────
# 헬퍼: 양력+음력 카드 텍스트+이미지 한번에 전송
# ─────────────────────────────────────────────
def _card_text_block(label: str, card_number: int, calendar_type: str) -> str:
    info = get_card_info(card_number)
    emoji = "☀️" if calendar_type == "양력" else "🌙"
    lines = [
        f"{emoji} *{label} ({calendar_type} 운명 카드)*\n",
        f"🔢 카드 번호: *{card_number}번*",
        f"🔎 *{info['name_kr']} ({info['name_en']})*",
    ]
    if info.get("description"):
        lines.append(f"\n{info['description']}")
    lines.append(f"🌟 *키워드:* {info['keywords']}")
    return "\n".join(lines)


async def send_cards_combined(message, label: str, solar_card: int, lunar_card: int = None):
    """양력+음력 카드를 텍스트 하나 + 이미지 묶음으로 전송"""
    solar_info = get_card_info(solar_card)
    lunar_info = get_card_info(lunar_card) if lunar_card is not None else None

    text = _card_text_block(label, solar_card, "양력")
    if lunar_card is not None and lunar_info:
        text += "\n\n─────────────────────\n\n"
        text += _card_text_block(label, lunar_card, "음력")
    await message.reply_text(text, parse_mode="Markdown")

    media_items = []
    solar_path = os.path.join(BASE_DIR, "images", f"{solar_card:02d}.jpg")
    if os.path.exists(solar_path):
        media_items.append((solar_path, f"☀️ {solar_info['name_kr']} ({solar_card}번)"))
    if lunar_card is not None and lunar_info:
        lunar_path = os.path.join(BASE_DIR, "images", f"{lunar_card:02d}.jpg")
        if os.path.exists(lunar_path):
            media_items.append((lunar_path, f"🌙 {lunar_info['name_kr']} ({lunar_card}번)"))

    if not media_items:
        logger.warning("send_cards_combined: 이미지 파일 없음")
        return

    if len(media_items) == 1:
        path, caption = media_items[0]
        with open(path, "rb") as f:
            await message.reply_photo(photo=f, caption=caption)
    else:
        combined_caption = "  |  ".join(cap for _, cap in media_items)
        file_handles = []
        photos = []
        for i, (path, _) in enumerate(media_items):
            f = open(path, "rb")
            file_handles.append(f)
            photos.append(InputMediaPhoto(
                media=f,
                caption=combined_caption if i == 0 else ""
            ))
        try:
            await message.get_bot().send_media_group(chat_id=message.chat_id, media=photos)
        except Exception as e:
            logger.error(f"send_media_group 실패 [{type(e).__name__}]: {e}")
            for path, cap in media_items:
                with open(path, "rb") as f:
                    await message.reply_photo(photo=f, caption=cap)
        finally:
            for f in file_handles:
                f.close()


# ─────────────────────────────────────────────
# 헬퍼: 생일 문자열 파싱
# ─────────────────────────────────────────────
def parse_birth_text(text: str):
    """
    입력: '홍길동 1990-05-20' 또는 '1990-05-20' 또는 '19900520'
    반환: (birth_clean 8자리, 'YYYY-MM-DD', name or None, error_msg or None)
    """
    parts = text.strip().split()
    name = None
    birth_str = text.strip()

    if len(parts) == 2 and any(c.isdigit() for c in parts[1]):
        name = parts[0]
        birth_str = parts[1]
    elif len(parts) == 1:
        birth_str = parts[0]

    birth_clean = birth_str.replace("-", "").replace(".", "").replace("/", "")
    if len(birth_clean) != 8 or not birth_clean.isdigit():
        return None, None, None, "❌ 날짜 형식이 올바르지 않아요.\n`YYYY-MM-DD` 또는 `YYYYMMDD`로 입력해주세요."

    y, m, d = birth_clean[:4], birth_clean[4:6], birth_clean[6:8]
    return birth_clean, f"{y}-{m}-{d}", name, None


# ═══════════════════════════════════════════════════════
# /start
# ═══════════════════════════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✨ *타로 운명 카드 봇에 오신 것을 환영합니다!*\n\n"
        "생년월일을 입력하면 *양력 카드*와 *음력 카드* 두 개를 알려드려요.\n\n"
        "아래 메뉴에서 원하는 기능을 선택하세요.",
        parse_mode="Markdown",
        reply_markup=MAIN_KEYBOARD,
    )
    return MENU


# ═══════════════════════════════════════════════════════
# 기능 1: 생일 → 운명 카드 (양력 + 음력)
# ═══════════════════════════════════════════════════════
async def menu_birth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "📅 *양력 생년월일을 입력해주세요.*\n\n"
        "형식: `YYYY-MM-DD` 또는 `YYYYMMDD`\n"
        "예시: `1990-05-20`\n\n"
        "이름도 저장하려면:\n"
        "`홍길동 1990-05-20` 형식으로 입력하세요.",
        parse_mode="Markdown",
    )
    return BIRTH_INPUT


async def handle_birth_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        birth_clean, birthday, name, err = parse_birth_text(update.message.text)
        if err:
            await update.message.reply_text(err, parse_mode="Markdown")
            return BIRTH_INPUT

        solar_card = calculate_destiny_card(birth_clean)
        display = f"*{name}* 님의 " if name else ""

        # 음력 자동 변환
        y, m, d = int(birth_clean[:4]), int(birth_clean[4:6]), int(birth_clean[6:8])
        lunar = solar_to_lunar(y, m, d)
        if lunar:
            lunar_clean = f"{lunar['year']:04d}{lunar['month']:02d}{lunar['day']:02d}"
            lunar_date  = f"{lunar['year']:04d}-{lunar['month']:02d}-{lunar['day']:02d}"
            leap_str = " (윤달)" if lunar.get("is_leap") else ""
            lunar_card = calculate_destiny_card(lunar_clean)
        else:
            lunar_clean = None
            lunar_date  = None
            leap_str    = ""
            lunar_card  = None

        await update.message.reply_text(
            f"☀️ {display}*양력 생일*: `{birthday}`\n"
            + (f"🌙 {display}*음력 생일*: `{lunar_date}`{leap_str}" if lunar_date else "⚠️ 음력 변환에 실패했어요."),
            parse_mode="Markdown"
        )

        await send_cards_combined(update.message, name or "운명", solar_card, lunar_card)

        # 구글 시트 저장
        if name:
            save_person(name, birthday, solar_card, lunar_date, lunar_card)

    except Exception as e:
        logger.error(f"handle_birth_input 오류: {e}", exc_info=True)

    await update.message.reply_text(
        "다른 기능을 이용하려면 아래 메뉴를 선택하세요.",
        reply_markup=MAIN_KEYBOARD
    )
    return MENU


# ═══════════════════════════════════════════════════════
# 기능 2: 이름으로 검색
# ═══════════════════════════════════════════════════════
async def menu_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(
        "🔍 *검색할 이름을 입력해주세요.*\n예시: `홍길동`",
        parse_mode="Markdown"
    )
    return NAME_SEARCH


async def handle_name_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = update.message.text.strip()
        results = find_person_by_name(name)

        if not results:
            await update.message.reply_text(
                f"❌ *{name}* 님의 정보를 찾을 수 없어요.\n\n"
                "생일 입력 메뉴에서 `이름 생년월일` 형식으로 저장할 수 있어요.",
                parse_mode="Markdown",
                reply_markup=MAIN_KEYBOARD
            )
            return MENU

        for person in results:
            si = get_card_info(person["solar_card"])
            li = get_card_info(person["lunar_card"]) if person.get("lunar_card") is not None else None

            summary = (
                f"👤 *{person['name']}*\n\n"
                f"☀️ 양력: `{person.get('solar_date', '-')}` → {si['name_kr']} ({person['solar_card']}번)\n"
            )
            if li and person.get("lunar_date"):
                summary += f"🌙 음력: `{person['lunar_date']}` → {li['name_kr']} ({person['lunar_card']}번)\n"
            await update.message.reply_text(summary, parse_mode="Markdown")

            await send_cards_combined(update.message, person["name"], person["solar_card"], person.get("lunar_card"))

    except Exception as e:
        logger.error(f"handle_name_search 오류: {e}", exc_info=True)

    await update.message.reply_text(
        "다른 기능을 이용하려면 아래 메뉴를 선택하세요.",
        reply_markup=MAIN_KEYBOARD
    )
    return MENU


# ═══════════════════════════════════════════════════════
# 기능 3: 두 사람 궁합
# ═══════════════════════════════════════════════════════
async def menu_compat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.message.reply_text(
        "💞 *첫 번째 사람* 양력 생년월일을 입력해주세요.\n\n"
        "형식: `이름 YYYY-MM-DD` 또는 `YYYY-MM-DD`\n"
        "저장된 이름만 입력해도 돼요: `홍길동`",
        parse_mode="Markdown"
    )
    return COMPAT_FIRST


def _auto_lunar_card(birth_clean: str):
    """양력 8자리 문자열로 음력 카드 번호 반환. 변환 실패 시 None."""
    y, m, d = int(birth_clean[:4]), int(birth_clean[4:6]), int(birth_clean[6:8])
    lunar = solar_to_lunar(y, m, d)
    if not lunar:
        return None, None, None
    lc = f"{lunar['year']:04d}{lunar['month']:02d}{lunar['day']:02d}"
    ld = f"{lunar['year']:04d}-{lunar['month']:02d}-{lunar['day']:02d}"
    leap_str = " (윤달)" if lunar.get("is_leap") else ""
    return calculate_destiny_card(lc), ld, leap_str


async def handle_compat_first(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    # 이름만 입력 → 시트 검색
    if len(parts) == 1 and not any(c.isdigit() for c in text):
        results = find_person_by_name(text)
        if results:
            p = results[0]
            context.user_data["compat_first"] = {
                "name": p["name"], "solar_card": p["solar_card"], "lunar_card": p.get("lunar_card"),
            }
            await _compat_first_done(update.message, context)
            return COMPAT_SECOND_INPUT
        await update.message.reply_text(f"❌ '{text}' 님을 찾을 수 없어요. 생년월일도 함께 입력해주세요.")
        return COMPAT_FIRST

    birth_clean, birthday, name, err = parse_birth_text(text)
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return COMPAT_FIRST

    solar_card = calculate_destiny_card(birth_clean)
    lunar_card, lunar_date, leap_str = _auto_lunar_card(birth_clean)
    context.user_data["compat_first"] = {
        "name": name or birthday, "solar_card": solar_card, "lunar_card": lunar_card,
    }
    await _compat_first_done(update.message, context)
    return COMPAT_SECOND_INPUT


async def _compat_first_done(message, context):
    first = context.user_data["compat_first"]
    sc = get_card_info(first["solar_card"])
    lc = get_card_info(first["lunar_card"]) if first.get("lunar_card") is not None else None
    lunar_line = f"\n🌙 음력 카드: {lc['name_kr']} ({first['lunar_card']}번)" if lc else ""
    await message.reply_text(
        f"✅ 첫 번째: *{first['name']}*\n"
        f"☀️ 양력 카드: {sc['name_kr']} ({first['solar_card']}번)"
        f"{lunar_line}\n\n"
        f"이제 *두 번째 사람* 양력 생년월일을 입력해주세요.\n"
        f"형식: `이름 YYYY-MM-DD` 또는 저장된 이름만 입력",
        parse_mode="Markdown"
    )


async def handle_compat_second(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) == 1 and not any(c.isdigit() for c in text):
        results = find_person_by_name(text)
        if results:
            p = results[0]
            context.user_data["compat_second"] = {
                "name": p["name"], "solar_card": p["solar_card"], "lunar_card": p.get("lunar_card"),
            }
            await _finish_compat(update.message, context)
            return MENU
        await update.message.reply_text(f"❌ '{text}' 님을 찾을 수 없어요. 생년월일도 함께 입력해주세요.")
        return COMPAT_SECOND_INPUT

    birth_clean, birthday, name, err = parse_birth_text(text)
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return COMPAT_SECOND_INPUT

    solar_card = calculate_destiny_card(birth_clean)
    lunar_card, lunar_date, leap_str = _auto_lunar_card(birth_clean)
    context.user_data["compat_second"] = {
        "name": name or birthday, "solar_card": solar_card, "lunar_card": lunar_card,
    }
    await _finish_compat(update.message, context)
    return MENU


async def _finish_compat(message, context):
    first  = context.user_data["compat_first"]
    second = context.user_data["compat_second"]

    sc1 = get_card_info(first["solar_card"])
    sc2 = get_card_info(second["solar_card"])
    lc1 = get_card_info(first["lunar_card"])  if first.get("lunar_card")  is not None else None
    lc2 = get_card_info(second["lunar_card"]) if second.get("lunar_card") is not None else None

    compat = get_compatibility(first["solar_card"], second["solar_card"])

    def cline(info, num): return f"{info['name_kr']} ({num}번)" if info else "미입력"

    msg = (
        f"💞 *궁합 분석 결과*\n\n"
        f"👤 *{first['name']}*\n"
        f"  ☀️ {cline(sc1, first['solar_card'])}\n"
        f"  🌙 {cline(lc1, first['lunar_card']) if lc1 else '미입력'}\n\n"
        f"👤 *{second['name']}*\n"
        f"  ☀️ {cline(sc2, second['solar_card'])}\n"
        f"  🌙 {cline(lc2, second['lunar_card']) if lc2 else '미입력'}\n\n"
        f"─────────────────\n"
        f"🌟 *궁합 에너지:* {compat['energy']}\n\n"
        f"{compat['description']}"
    )
    await message.reply_text(msg, parse_mode="Markdown")

    for label, card_num in [
        (f"{first['name']} ☀️",  first["solar_card"]),
        (f"{first['name']} 🌙",  first.get("lunar_card")),
        (f"{second['name']} ☀️", second["solar_card"]),
        (f"{second['name']} 🌙", second.get("lunar_card")),
    ]:
        if card_num is not None:
            img_path = os.path.join(BASE_DIR, "images", f"{card_num:02d}.jpg")
            if os.path.exists(img_path):
                info = get_card_info(card_num)
                with open(img_path, "rb") as img:
                    await message.reply_photo(photo=img, caption=f"🃏 {label}: {info['name_kr']}")

    await message.reply_text("다른 기능을 이용하려면 아래 메뉴를 선택하세요.", reply_markup=MAIN_KEYBOARD)


# ═══════════════════════════════════════════════════════
# 봇 실행
# ═══════════════════════════════════════════════════════
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 환경변수가 설정되지 않았습니다.")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        allow_reentry=True,
        states={
            MENU: [
                CallbackQueryHandler(menu_birth,  pattern="^menu_birth$"),
                CallbackQueryHandler(menu_name,   pattern="^menu_name$"),
                CallbackQueryHandler(menu_compat, pattern="^menu_compat$"),
            ],
            BIRTH_INPUT:        [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_birth_input)],
            NAME_SEARCH:        [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name_search)],
            COMPAT_FIRST:       [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_compat_first)],
            COMPAT_SECOND_INPUT:[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_compat_second)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(conv)
    logger.info("봇이 시작되었습니다!")
    app.run_polling()


if __name__ == "__main__":
    main()
