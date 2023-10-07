from tg_bot.keyboards.inline_menu_keyboard import (
    make_main_menu_keyboard,
    make_files_menu_keyboard,
    make_file_page_keyboard,
    MenuCallbackData,
)
from aiogram import types
from aiogram import Router

from ..global_const import (
    DIRECTORY_FOR_PHOTOS,
    MAIN_MENU_PHOTO,
    MAIN_MENU_TEXT,
    FILES_MENU_PHOTO,
    FILES_MENU_TEXT,
    DIRECTORY_FOR_TEMPLATES,
    FILE_PAGE_TEXT,
)
from ..global_const import (
    get_buffer_of_photos,
    update_photo_buffer,
    get_buffer_of_documents,
    update_document_buffer,
)

menu_router = Router()


async def main_menu_proceccing(callback: types.CallbackQuery, bot, **kwargs):
    """
    Отрисовывает главное меню, изменяя текст и клавиатуру сообщения,
    от которого пришёл callback запрос (или того, что подано на вход функции),
    на те, что должны отражаться в главном меню.

        Параметры:
            callback (CallbackQuery или Message): входящий callback запрос, ведущий в главное меню
    """

    # Создаём клавиатуру главного меню
    markup = await make_main_menu_keyboard()

    # Загружаем буфер подгруженных фотографий и собираем полное имя фото,
    # которое будет отображаться в главном меню
    photo_buffer = await get_buffer_of_photos()
    photo_name = DIRECTORY_FOR_PHOTOS + MAIN_MENU_PHOTO

    # FIX ME: сделать автоматическую подгрузку фото перед началом работы бота в буфер
    # и убрать проверку на наличие фото в нём

    # Проверяем какой тип данных пришёл на вход (callback или message)
    # и изменяем у соответствующего сообщения текст, фото и клавиатуру на требуемые
    if photo_name in photo_buffer:
        photo = photo_buffer[photo_name]
    else:
        photo = types.FSInputFile(photo_name, filename=photo_name)

    if isinstance(callback, types.CallbackQuery):
        message = await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=types.InputMediaPhoto(media=photo, caption=MAIN_MENU_TEXT),
            reply_markup=markup,
        )
    else:
        message = await bot.send_photo(
            chat_id=callback.chat.id,
            photo=photo,
            caption=MAIN_MENU_TEXT,
            reply_markup=markup,
        )

    if photo_name not in photo_buffer:
        await update_photo_buffer(photo_name, message.photo[-1].file_id)


async def files_menu_proceccing(
    callback: types.CallbackQuery, category: str, bot, **kwargs
):
    """
    Отрисовывает меню файлов выбранной категории, изменяя текст и клавиатуру сообщения,
    от которого пришёл callback запрос, на те, что должны отражаться в меню файлов.

        Параметры:
            callback (CallbackQuery): входящий callback запрос, ведущий в главное меню
            category (str): выбранный подраздел меню
    """

    # Создаём клавиатуру требуемой страницы меню файлов
    markup = await make_files_menu_keyboard(category)

    # Загружаем буфер подгруженных фотографий и собираем полное имя фото, которое будет отображаться на
    # требуемой странице меню файлов
    photo_buffer = await get_buffer_of_photos()
    photo_name = DIRECTORY_FOR_PHOTOS + FILES_MENU_PHOTO

    # FIX ME: сделать автоматическую подгрузку фото перед началом работы бота в буфер
    # и убрать проверку на наличие фото в нём

    # Изменяем у сообщения, от которого поступил callback запрос, текст, фото и клавиатуру на требуемые
    if photo_name in photo_buffer:
        photo = photo_buffer[photo_name]
    else:
        photo = types.FSInputFile(photo_name, filename=photo_name)

    message = await bot.edit_message_media(
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        media=types.InputMediaPhoto(media=photo, caption=FILES_MENU_TEXT),
        reply_markup=markup,
    )

    if photo_name not in photo_buffer:
        await update_photo_buffer(photo_name, message.photo[-1].file_id)


async def file_page_proceccing(
    callback: types.CallbackQuery, category: str, document_name: str, bot, **kwargs
):
    """
    Отрисовывает меню конкретного файла, добавляя клавиатуру с надписями 'Назад' и 'Заполнить',
    соответствующий текст и прикрепляя пустой шаблон выбранного файла к сообщению.

        Параметры:
            callback (CallbackQuery или Message): входящий callback запрос, ведущий в главное меню
            category (str): выбранный подраздел меню
            document_name (str): название выбранного файла

    """

    # Создаём клавиатуру под выбранным файлом
    markup = await make_file_page_keyboard(
        category=category, document_name=document_name
    )

    # Загружаем буфер подгруженных документов и собираем полное имя файла,
    # который будет прикреплен к сообщению
    documents_buffer = await get_buffer_of_documents()
    document_name = f"{DIRECTORY_FOR_TEMPLATES}{document_name}.pdf"

    # FIX ME: сделать автоматическую подгрузку файлов перед началом работы бота в буфер
    # и убрать проверку на наличие файла в нём

    # Изменяем у сообщения, от которого поступил callback запрос, текст и клавиатуру на требуемые
    # и прикрепляем нужный файл вместо фотографии
    if document_name in documents_buffer:
        document = documents_buffer[document_name]
    else:
        document = types.FSInputFile(document_name, filename=document_name)

    if isinstance(callback, types.CallbackQuery):
        message = await bot.edit_message_media(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            media=types.InputMediaDocument(media=document, caption=FILE_PAGE_TEXT),
            reply_markup=markup,
        )
    else:
        message = await bot.send_document(
            chat_id=callback.chat.id,
            document=document,
            caption=FILE_PAGE_TEXT,
            reply_markup=markup,
        )

    if document_name not in documents_buffer:
        await update_document_buffer(document_name, message.document.file_id)


@menu_router.callback_query(MenuCallbackData.filter())
async def navigate(callback: types.CallbackQuery, callback_data: MenuCallbackData, bot):
    """
    Функция, обрабатывающая callback запросы от инлайн клавиатуры меню и
    осуществляющая навигацию по этому меню

        Параметры:
            callback (CallbackQuery): принятый callback запрос, отправленный нажатой кнопкой меню
            callback_data (MenuCallbackData): данные, переданные с callback запросом

    """

    # Создаём словарь соответствий уровня вложенности меню и функций-обработчиков страниц меню
    levels = {
        0: main_menu_proceccing,
        1: files_menu_proceccing,
        2: file_page_proceccing,
    }

    # Выбираем нужную функцию обработчий по значению уровня вложенности. Уровень
    # получаем из соответствующего поля callback_data
    current_level_function = levels[callback_data.level]

    # Вызываем выбранную функцию-обработчик, передавая в неё соответствующие данные о разделе меню,
    # выбранном документе и уровне вложенности, которые хранятся в пришедшей callback_data
    await current_level_function(
        callback,
        category=callback_data.category,
        document_name=callback_data.document_name,
        bot=bot,
    )

    # Отвечаем на callback запрос
    await callback.answer()
