from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def generate_inline_keyboard(
    buttons_data: list[tuple[str, str]],
    row_widths: list[int] = None
) -> InlineKeyboardMarkup:
    """
    Генерация инлайн-клавиатуры с помощью InlineKeyboardBuilder.

    :param buttons_data: Список кортежей (текст_кнопки, callback_data)
    :param row_widths: Список, задающий количество кнопок в рядах.
                       Например, [2, 1] создаст ряд с 2 кнопками и следующий с 1.
                       Если None — все кнопки будут в один ряд.
    :return: InlineKeyboardMarkup для отправки ботом.
    """
    builder = InlineKeyboardBuilder()
    
    for text, callback in buttons_data:
        builder.button(text=text, callback_data=callback)
    
    if row_widths:
        builder.adjust(*row_widths)
    
    return builder.as_markup()

