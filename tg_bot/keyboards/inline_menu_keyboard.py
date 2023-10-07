from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters.callback_data import CallbackData
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..global_const import KEYBOARD_WIDTH, LEXICON
from ..global_const import get_catigories, get_documents


class MenuCallbackData(CallbackData, prefix="menu"):
    """
    Фабрика коллбэков для навигации по меню. Содержит в себе следущую информацию

    level: уровень вложенности меню
    category: текущая категория
    document_id: название текущего документа
    """

    level: int
    category: str
    document_name: str


class FillDocumentCallbackData(CallbackData, prefix="fill"):
    """
    Фабрика коллбэков для заполнения документа. Содержит в себе следущую информацию

    category: текущая категория
    document_id: текущий документ
    """

    category: str
    document_name: str


# Собирает CallbsckData с нужной информацией
async def make_callback_data(
    level: int, category: str = "0", document_name: str = "0"
) -> MenuCallbackData:
    return MenuCallbackData(level=level, category=category, document_name=document_name)


async def make_main_menu_keyboard(**kwargs) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн клавиатуру главного меню

        Параметры:
            Нет

        Возвращаемое значение:
            keyboardb_builder.as_markup() (InlineKeyboardMarkup): инлайн клавиатура главного меню
    """

    # Задаём текущий уровень вложенности
    CURRENT_LEVEL = 0

    # Получаем набор категорий, которые необходимо отразить в меню
    categories = await get_catigories()

    # Создаём билдер будущей клавиатуры и лист кнопок в ней
    keyboardb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    # Для каждой категории создаём кнопку и добавляем её в массив кнопок buttons
    for category in categories:
        text = LEXICON[category]
        callback_data = await make_callback_data(
            level=CURRENT_LEVEL + 1, category=category
        )

        buttons.append(
            InlineKeyboardButton(text=text, callback_data=callback_data.pack())
        )

    # Собираем клавиатуру требуемой ширины и возвращаем её
    keyboardb_builder.row(*buttons, width=KEYBOARD_WIDTH)

    return keyboardb_builder.as_markup()


async def make_files_menu_keyboard(category: str, **kwargs) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн клавиатуру меню файлов

        Параметры:
            category (str): имя текущего подраздела с файлами

        Возвращаемое значение:
            keyboardb_builder.as_markup() (InlineKeyboardMarkup): инлайн клавиатура меню файлов
    """

    # Задаём текущий уровень вложенности
    CURRENT_LEVEL = 1

    # Получаем набор документов, которые необходимо отразить в меню
    documents = await get_documents(category)

    # Создаём билдер будущей клавиатуры и лист кнопок в ней
    keyboardb_builder = InlineKeyboardBuilder()
    buttons: list[InlineKeyboardButton] = []

    # Для каждой категории создаём кнопку и добавляем её в массив кнопок buttons
    for document in documents:
        text = LEXICON[document]
        callback_data = await make_callback_data(
            level=CURRENT_LEVEL + 1, category=category, document_name=document
        )

        buttons.append(
            InlineKeyboardButton(text=text, callback_data=callback_data.pack())
        )

    # Создаём кнопку 'Назад' для возврата в главное меню и добавляем её в массив buttons
    text = "Назад"
    callback_data = await make_callback_data(level=CURRENT_LEVEL - 1)
    buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data.pack()))

    # Собираем клавиатуру требуемой ширины и возвращаем её
    keyboardb_builder.row(*buttons, width=KEYBOARD_WIDTH)

    return keyboardb_builder.as_markup()


async def make_file_page_keyboard(
    category: str, document_name: str, **kwargs
) -> InlineKeyboardMarkup:
    """
    Генерирует инлайн клавиатуру на странице конкретного файла

        Параметры:
            category (str): имя текущего подраздела с файлами
            document_name (str): название текущего файла

        Возвращаемое значение:
            keyboardb_builder.as_markup() (InlineKeyboardMarkup): инлайн клавиатура меню файлов
    """

    # Задаём текущий уровень вложенности
    CURRENT_LEVEL = 2

    # Создаём билдер будущей клавиатуры
    keyboardb_builder = InlineKeyboardBuilder()

    # Создаём кнопку 'Заполнить документ' для возврата в главное меню и добавляем её в массив buttons
    text = "Заполнить документ"
    callback_data = FillDocumentCallbackData(
        category=category, document_name=document_name
    )
    fill_button = InlineKeyboardButton(text=text, callback_data=callback_data.pack())

    # Создаём кнопку 'Назад' для возврата в главное меню и добавляем её в массив buttons
    text = "Назад"
    callback_data = await make_callback_data(level=CURRENT_LEVEL - 1, category=category)
    back_button = InlineKeyboardButton(text=text, callback_data=callback_data.pack())

    # Собираем клавиатуру требуемой ширины и возвращаем её
    keyboardb_builder.row(fill_button, back_button, width=1)

    return keyboardb_builder.as_markup()
