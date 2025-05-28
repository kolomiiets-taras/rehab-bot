from app.telegram_bot.bot import bot
from aiogram.utils.markdown import html_decoration as hd
from app.config import app_config
from aiogram.types import Message, FSInputFile
from app.telegram_bot.keyboards.session_keyboards import skip_start_keyboard, next_step_keyboard, finish_keyboard


async def send_exercise(
    message: Message, session_id: int, title: str, text: str, media: str | None = None, last: bool = False
) -> None:
    message_text = f"🔹<b>{hd.quote(title)}</b>🔹\n\n{hd.quote(text)}"
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


async def send_session(chat_id: int, session_id: int) -> None:
    message_text = f"🔹<b>{hd.quote('Start session')}</b>🔹"

    await bot.send_message(
        chat_id=chat_id,
        text=message_text,
        parse_mode="HTML",
        reply_markup=skip_start_keyboard(session_id=session_id)
    )
