from logger import logger
from telegram_bot.bot import bot
from aiogram.utils.markdown import html_decoration as hd
from config import app_config
from aiogram.types import Message, FSInputFile
from telegram_bot.keyboards.session_keyboards import skip_start_keyboard, next_step_keyboard, finish_keyboard
from telegram_bot.middlewares.localization import i18n
import re


def clean_html_for_telegram(html: str) -> str:
    # Заменяем <br> и <br/> на перевод строки
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)

    # Заменяем <p> на новую строку (с обоих сторон)
    html = re.sub(r'</p>\s*<p>', '\n', html)  # между параграфами
    html = re.sub(r'<p[^>]*>', '', html)      # открывающие теги <p>
    html = re.sub(r'</p>', '\n', html)        # закрывающие теги </p>

    # Удаляем все теги, кроме разрешённых
    allowed_tags = ['b', 'strong', 'i', 'em', 'u', 's', 'strike', 'del', 'code', 'span']
    html = re.sub(r'</?(?!' + '|'.join(allowed_tags) + r')\w+[^>]*>', '', html)

    # Удаляем span, кроме тех у которых class="tg-spoiler"
    html = re.sub(r'<span(?![^>]*class="tg-spoiler")[^>]*>(.*?)</span>', r'\1', html)

    # Очистка лишних пробелов и пустых строк
    html = re.sub(r'[ \t]+\n', '\n', html)
    html = re.sub(r'\n[ \t]+', '\n', html)
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html.strip()


async def send_exercise(
    message: Message, session_id: int, title: str, text: str, media: str | None = None, last: bool = False
) -> None:
    message_text = f"🔹<b>{hd.quote(title)}</b>🔹\n\n{clean_html_for_telegram(text)}"
    keyboard = finish_keyboard if last else next_step_keyboard
    kwargs = {'caption': message_text, 'parse_mode': 'HTML', 'reply_markup': keyboard(session_id=session_id)}

    if media:
        media_file = FSInputFile(app_config.MEDIA_PATH / media)
        if media.lower().endswith(".mp4"):
            method = message.answer_video
            kwargs['video'] = media_file
        else:
            method = message.answer_photo
            kwargs['photo'] = media_file
    else:
        method = message.answer

    await method(**kwargs)


async def send_session(
    chat_id: int,
    session_id: int,
    locale: str,
    course_title: str,
    session_number: int,
    total_sessions: int
) -> None:
    message_text = i18n.gettext('session.header', locale=locale).format(
        course_title=course_title, session_number=session_number, total_sessions=total_sessions
    )

    await bot.send_message(
        chat_id=chat_id,
        text=message_text,
        parse_mode="HTML",
        reply_markup=skip_start_keyboard(session_id=session_id, locale=locale)
    )
    logger.info(f"Session started for user tg_id: {chat_id}. Session ID: {session_id}, Course: {course_title}")
    await bot.session.close()
