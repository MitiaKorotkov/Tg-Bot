from ..keyboards.inline_menu_keyboard import FillDocumentCallbackData
from ..misc.states import FSMFillPersonalData
from .menu_handlers import file_page_proceccing

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.filters import StateFilter
from aiogram import types
from aiogram import Router

from jinja2 import Environment, FileSystemLoader
import subprocess
import os

from ..global_const import (
    CHAINS_OF_STATES,
    LEXICON,
    DIRECTORY_FOR_PHOTOS,
    DOWNLOAD_PHOTO,
    DIRECTORY_FOR_LATEX_FILES,
    WITH_FILL_FILE_MESSAGE,
    DIRECTORY_FOR_TEMPLATES,
)
from ..global_const import update_photo_buffer, get_buffer_of_photos


fsm_router = Router()


async def fill_template(user_data: dict, document_name: str):
    """
    Заполняет теховский шаблон данными пользователя и создаёт соответствующий
    .pdf документ.

        Параметры:
            user_data (): словарь, содержащий необходимые данные пользователя
            document_name (): название файла, шаблон которого необходимо заполнить

        Возвращаемое значение:
            Возвращает корутину
    """

    # С помощью jinja загружаем теховский шаблон из файловой системы и
    # подставляем в нужные места данные пользователя
    environment = Environment(loader=FileSystemLoader(DIRECTORY_FOR_TEMPLATES))
    template = environment.get_template(f"{document_name}.tex")
    filled_file = template.render(user_data=user_data)

    # Записываем заполненный шаблон в теховский файл
    filename = f'{DIRECTORY_FOR_LATEX_FILES}file_for_user{user_data["id"]}'
    with open(f"{filename}.tex", "w", encoding="utf-8") as file:
        file.write(filled_file)

    # Собираем полученный теховский файл
    subprocess.call(
        f"xelatex -output-directory={DIRECTORY_FOR_LATEX_FILES} {filename}.tex"
    )

    # Очищаем директорию ото всех временных теховских файлов
    if os.path.isfile(f"{filename}.aux"):
        os.unlink(f"{filename}.aux")
    if os.path.isfile(f"{filename}.idx"):
        os.unlink(f"{filename}.idx")
    if os.path.isfile(f"{filename}.log"):
        os.unlink(f"{filename}.log")
    if os.path.isfile(f"{filename}.tex"):
        os.unlink(f"{filename}.tex")


@fsm_router.callback_query(
    FillDocumentCallbackData.filter(), StateFilter(default_state)
)
async def fill_document(
    callback: types.CallbackQuery,
    callback_data: FillDocumentCallbackData,
    state: FSMContext,
):
    """
    Функция входа в машину состояний. Активируется при callback запросе, содержащим FillDocumentCallbackData callback_data,
    отправляемую при нажатии на кнопку 'Заполнить документ'. Функция инициализирует хранилище для сбора данных, загружает
    последовательность токенов, соответствующую выбранному документу и запускает машину состояний, переводя её во второе
    состояние из этой цепочки.

        Параметры:
            callback (CallbackQuery):
            callback_data (FillDocumentCallbackData):
            state (FSMContext):

    """

    # Инициализируем словарь с даными пользователя, сохраняя туда информацию, которая потебуется
    # в дальнейшем для возврата в меню и заполнения выбранного зокумента и загружаем его в хранилище
    user_data = {
        "chain_of_states": CHAINS_OF_STATES[callback_data.document_name],
        "document_name": callback_data.document_name,
        "category": callback_data.category,
        "id": callback.from_user.id,
        "iteration": 0,
    }
    await state.update_data(user_data)

    # Устанавливаем следующее состояние для FSM -- первое в цепочке токенов
    next_state = user_data["chain_of_states"][0]

    # Удаляем клавиатуру меню и выводим сообщение с приглашением ввести первый токен из цепочки
    await callback.message.delete_reply_markup()
    await callback.message.answer(text=f"Введите {LEXICON[next_state]}")

    # Переводим машину состояний в промежуточное состояние -- состояние ввода данных
    await state.set_state(FSMFillPersonalData.middle_state)

    # Отвечаем на callback
    await callback.answer()


@fsm_router.message(StateFilter(FSMFillPersonalData.middle_state))
async def process_name_sent(message: types.Message, state: FSMContext):
    """
    Считывает введённые пользователем данные, просит ввести пользователя следующий токен
    и переводит FSN в следующее состояние.

        Параметры:
            message (types.Message): сообщение от пользователя, с введённым значением предыдущего токена
            state (FSMContext): данные FSM
    """

    # Получаем данные пользователя из хранилища
    user_data = await state.get_data()

    # Записываем в словарь данных пользователя введённую пользователем информацию о текущем токене
    current_state = user_data["chain_of_states"][user_data["iteration"]]
    user_data[current_state] = message.text

    # Достаём из цепочки токенов токен, следующий за текущим
    user_data["iteration"] += 1
    next_state = user_data["chain_of_states"][user_data["iteration"]]

    # Обновляем данные в хранилище и выводим сообщение с приглашением ввести следующий токен
    await state.update_data(user_data)
    await message.answer(text=f"Введите {LEXICON[next_state]}")

    # Переводим FSM в следующее состояние, конечное (если цепочка закончилась)
    # или ввода токенов (если она продолжается)
    await state.set_state(
        FSMFillPersonalData.final_state
        if next_state == "final_state"
        else FSMFillPersonalData.middle_state
    )


@fsm_router.message(StateFilter(FSMFillPersonalData.final_state))
async def process_final_state_sent(message: types.Message, state: FSMContext, bot):
    """
    Обрабатывает финальное состояние FSM. Создаёт и отправляет пользователю документ,
    заполненный его данными и возвращает его в меню документов. Выходит из FSM,
    переводя её в состояние по умолчанию.

        Параметры:
            message (types.Message): сообщение от пользователя, с введённым значением токена -- желаемого имени файла
            state (FSMContext): данные FSM
    """

    # Достаём данные пользователя (введённые им ранее) из хранилища и
    # запоминаем название файла для пользователя
    user_data = await state.get_data()
    filename = message.text

    #  Просим пользователя подождать и генерируем требуемый pdf документ,
    # заполненный данными пользователя
    photo_buffer = await get_buffer_of_photos()
    photo_name = DIRECTORY_FOR_PHOTOS + DOWNLOAD_PHOTO
    if photo_name in photo_buffer:
        photo = photo_buffer[photo_name]
    else:
        photo = types.FSInputFile(photo_name, filename=photo_name)

    message = await bot.send_photo(
        chat_id=message.chat.id, photo=photo, caption=LEXICON["wait"]
    )

    if photo_name not in photo_buffer:
        await update_photo_buffer(photo_name, message.photo[-1].file_id)

    await fill_template(user_data=user_data, document_name=user_data["document_name"])

    # Cобираем полное имя pdf файла, сгенерированного функцией fill_template
    document_name = f'{DIRECTORY_FOR_LATEX_FILES}file_for_user{user_data["id"]}.pdf'

    # Отправляем пользователю сообщение с прикреплённым к нему заполненным файлом
    # При этом меняем его название на то, которое было введено пользователем
    await bot.send_document(
        chat_id=message.chat.id,
        document=types.FSInputFile(document_name, filename=f"{filename}.pdf"),
        caption=WITH_FILL_FILE_MESSAGE,
    )

    # Удаляем отправленный файл с компьютера, чтобы не засорять директорию
    if os.path.isfile(document_name):
        os.unlink(document_name)

    # Возвращаем пользователя на страницу меню файла, который был заполнен
    await file_page_proceccing(
        message,
        category=user_data["category"],
        document_name=user_data["document_name"],
        bot=bot,
    )

    # Очишаем машину состояний (выходим из неё в состояние по умолчанию)
    await state.clear()
