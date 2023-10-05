from aiogram import Bot, Dispatcher
import asyncio

from aiogram import types
from aiogram.types import InlineKeyboardButton, InputMediaDocument, InputMediaPhoto
from aiogram.fsm.state import default_state, State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData
from aiogram.filters import CommandStart, StateFilter

from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv
import subprocess
import os


class FSMFillPersonalData(StatesGroup):
    '''
    Это класс с состояниями машины состояний.

    middle_state: состояние ввода персональных данных
    final_state: состояние выхода из машины состояний
    '''
    middle_state = State()
    final_state = State()


class MenuCallbackData(CallbackData, prefix='menu'):
    '''
    Фабрика коллбэков для навигации по меню. Содержит в себе следущую информацию

    level: уровень вложенности меню
    category: текущая категория
    document_id: название текущего документа
    '''

    level: int
    category: str
    document_name: str


class FillDocumentCallbackData(CallbackData, prefix='fill'):
    '''
    Фабрика коллбэков для заполнения документа. Содержит в себе следущую информацию

    category: текущая категория
    document_id: текущий документ
    '''

    category: str
    document_name: str


load_dotenv()
TOKEN_API = os.getenv('BOT_TOKEN')

DESCRIPTION = '''Описание этого бота и его команд'''
MAIN_MENU_TEXT = '''Вот такие группы заявлений у меня есть'''
FILES_MENU_TEXT = '''В данном разделе есть следующие файлы'''
FILE_PAGE_TEXT = '''Вот пустой бланк. Можете заполнить его сами или попросить об этом меня'''
WITH_FILL_FILE_MESSAGE = '''Вот ваш заполненный файл'''

DIRECTORY_FOR_LATEX_FILES = 'database/tmp_latex_files/'
DIRECTORY_FOR_TEMPLATES = 'database/templates/'
DIRECTORY_FOR_PHOTOS = 'database/photos/'

MAIN_MENU_PHOTO = 'main_menu_photo.jpg'
FILES_MENU_PHOTO = 'submenu_photo.jpg'
DOWNLOAD_PHOTO = 'download_photo.jpg'

# Словарь последовательностей токенов для доступных документов.
# Распололжение токенов в последовательности совпадает с их порядком заполнения
CHAINS_OF_STATES = {'diploma_cover': ['name', 'surname', 'patronimic', 'final_state'],
                    'only_text': ['name', 'final_state']
                    }

# Структура меню
CATEGORIES = {'Category 1': ['diploma_cover'],
              'Category 2': ['only_text', 'diploma_cover']
              }

# Словарь для русификации
LEXICON = {'Category 1': 'Категория 1',
           'Category 2': 'Категория 2',
           'Category 3': 'Категория 3',
           'Category 4': 'Категория 4',
           'diploma_cover': 'Титульник',
           'only_text': 'Просто текст',
           'Back button': 'Назад',
           'Fill document button': 'Заполнить документ',
           'wait': 'Пожалуйста, подождите немного, документ готовится',
           'name': 'имя',
           'surname': 'фамилию',
           'patronimic': 'отчество',
           'birth_date': 'дату рождения',
           'final_state': 'название документа'
           }

# Буфферы для id уже загруженных фото и документов
DOCUMENTS_BUFFER = {}
PHOTO_BUFFER = {}

# Желаемое число кнопок в ряду инлайн клавиатуры меню
KEYBOARD_WIDTH = 3

# Инициализация бота и диспетчера

bot = Bot(token=TOKEN_API)
dp = Dispatcher()

async def fill_template(user_data: dict, document_name: str):
    '''
    Заполняет теховский шаблон данными пользователя и создаёт соответствующий
    .pdf документ.

        Параметры:
            user_data (): словарь, содержащий необходимые данные пользователя
            document_name (): название файла, шаблон которого необходимо заполнить

        Возвращаемое значение:
            Возвращает корутину
    '''

    # С помощью jinja загружаем теховский шаблон из файловой системы и
    # подставляем в нужные места данные пользователя
    environment = Environment(loader=FileSystemLoader(DIRECTORY_FOR_TEMPLATES))
    template = environment.get_template(f'{document_name}.tex')
    filled_file = template.render(user_data=user_data)

    # Записываем заполненный шаблон в теховский файл
    filename = f'{DIRECTORY_FOR_LATEX_FILES}file_for_user{user_data["id"]}'
    with open(f'{filename}.tex', 'w', encoding='utf-8') as file:
        file.write(filled_file)

    # Собираем полученный теховский файл
    subprocess.call(
        f'xelatex -output-directory={DIRECTORY_FOR_LATEX_FILES} {filename}.tex')

    # Очищаем директорию ото всех временных теховских файлов
    if os.path.isfile(f'{filename}.aux'):
        os.unlink(f'{filename}.aux')
    if os.path.isfile(f'{filename}.idx'):
        os.unlink(f'{filename}.idx')
    if os.path.isfile(f'{filename}.log'):
        os.unlink(f'{filename}.log')
    if os.path.isfile(f'{filename}.tex'):
        os.unlink(f'{filename}.tex')


# Возвращает список категорий меню
async def get_catigories() -> list[str]:
    return CATEGORIES.keys()


# Возвращает список документов в данной категории
async def get_documents(category: str) -> list[str]:
    return CATEGORIES[category]


# Возвращает буффер загруженных фото
async def get_buffer_of_photos() -> dict:
    return PHOTO_BUFFER


# Возвращает буффер загруженных документов
async def get_buffer_of_documents() -> dict:
    return DOCUMENTS_BUFFER


# Обновляет буффер загруженных фото
async def update_photo_buffer(key: str, value: str):
    global PHOTO_BUFFER
    PHOTO_BUFFER[key] = value


# Обновляет буффер загруженных документов
async def update_document_buffer(key: str, value: str):
    global DOCUMENTS_BUFFER
    DOCUMENTS_BUFFER[key] = value


# Собирает CallbsckData с нужной информацией
async def make_callback_data(level: int, category: str = '0', document_name: str = '0') -> MenuCallbackData:
    return MenuCallbackData(level=level, category=category, document_name=document_name)

# .......................keyboards.....................................#


async def make_main_menu_keyboard(**kwargs) -> types.InlineKeyboardMarkup:
    '''
    Генерирует инлайн клавиатуру главного меню

        Параметры:
            Нет

        Возвращаемое значение:
            keyboardb_builder.as_markup() (InlineKeyboardMarkup): инлайн клавиатура главного меню
    '''

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
        callback_data = await make_callback_data(level=CURRENT_LEVEL + 1,
                                                 category=category)

        buttons.append(InlineKeyboardButton(text=text,
                                            callback_data=callback_data.pack()))

    # Собираем клавиатуру требуемой ширины и возвращаем её
    keyboardb_builder.row(*buttons, width=KEYBOARD_WIDTH)

    return keyboardb_builder.as_markup()


async def make_files_menu_keyboard(category: str, **kwargs) -> types.InlineKeyboardMarkup:
    '''
    Генерирует инлайн клавиатуру меню файлов

        Параметры:
            category (str): имя текущего подраздела с файлами

        Возвращаемое значение:
            keyboardb_builder.as_markup() (InlineKeyboardMarkup): инлайн клавиатура меню файлов
    '''

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
        callback_data = await make_callback_data(level=CURRENT_LEVEL + 1,
                                                 category=category,
                                                 document_name=document)

        buttons.append(InlineKeyboardButton(text=text,
                                            callback_data=callback_data.pack()))

    # Создаём кнопку 'Назад' для возврата в главное меню и добавляем её в массив buttons
    text = 'Назад'
    callback_data = await make_callback_data(level=CURRENT_LEVEL - 1)
    buttons.append(InlineKeyboardButton(text=text,
                                        callback_data=callback_data.pack()))

    # Собираем клавиатуру требуемой ширины и возвращаем её
    keyboardb_builder.row(*buttons, width=KEYBOARD_WIDTH)

    return keyboardb_builder.as_markup()


async def make_file_page_keyboard(category: str, document_name: str, **kwargs) -> types.InlineKeyboardMarkup:
    '''
    Генерирует инлайн клавиатуру на странице конкретного файла

        Параметры:
            category (str): имя текущего подраздела с файлами
            document_name (str): название текущего файла

        Возвращаемое значение:
            keyboardb_builder.as_markup() (InlineKeyboardMarkup): инлайн клавиатура меню файлов
    '''

    # Задаём текущий уровень вложенности
    CURRENT_LEVEL = 2

    # Создаём билдер будущей клавиатуры
    keyboardb_builder = InlineKeyboardBuilder()

    # Создаём кнопку 'Заполнить документ' для возврата в главное меню и добавляем её в массив buttons
    text = 'Заполнить документ'
    callback_data = FillDocumentCallbackData(category=category,
                                             document_name=document_name)
    fill_button = InlineKeyboardButton(text=text,
                                       callback_data=callback_data.pack())

    # Создаём кнопку 'Назад' для возврата в главное меню и добавляем её в массив buttons
    text = 'Назад'
    callback_data = await make_callback_data(level=CURRENT_LEVEL - 1, category=category)
    back_button = InlineKeyboardButton(text=text,
                                       callback_data=callback_data.pack())

    # Собираем клавиатуру требуемой ширины и возвращаем её
    keyboardb_builder.row(fill_button, back_button, width=1)

    return keyboardb_builder.as_markup()

# ................................callback_proccesing.................................#


async def main_menu_proceccing(callback: types.CallbackQuery, **kwargs):
    '''
    Отрисовывает главное меню, изменяя текст и клавиатуру сообщения,
    от которого пришёл callback запрос (или того, что подано на вход функции),
    на те, что должны отражаться в главном меню.

        Параметры:
            callback (CallbackQuery или Message): входящий callback запрос, ведущий в главное меню
    '''

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
        message = await bot.edit_message_media(chat_id=callback.message.chat.id,
                                               message_id=callback.message.message_id,
                                               media=InputMediaPhoto(media=photo,
                                                                     caption=MAIN_MENU_TEXT),
                                               reply_markup=markup)
    else:
        message = await bot.send_photo(chat_id=callback.chat.id,
                                       photo=photo,
                                       caption=MAIN_MENU_TEXT,
                                       reply_markup=markup)

    if photo_name not in photo_buffer:
        await update_photo_buffer(photo_name, message.photo[-1].file_id)


async def files_menu_proceccing(callback: types.CallbackQuery, category: str, **kwargs):
    '''
    Отрисовывает меню файлов выбранной категории, изменяя текст и клавиатуру сообщения,
    от которого пришёл callback запрос, на те, что должны отражаться в меню файлов.

        Параметры:
            callback (CallbackQuery): входящий callback запрос, ведущий в главное меню
            category (str): выбранный подраздел меню
    '''

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

    message = await bot.edit_message_media(chat_id=callback.message.chat.id,
                                           message_id=callback.message.message_id,
                                           media=InputMediaPhoto(media=photo,
                                                                 caption=FILES_MENU_TEXT),
                                           reply_markup=markup)

    if photo_name not in photo_buffer:
        await update_photo_buffer(photo_name, message.photo[-1].file_id)


async def file_page_proceccing(callback: types.CallbackQuery, category: str, document_name: str, **kwargs):
    '''
    Отрисовывает меню конкретного файла, добавляя клавиатуру с надписями 'Назад' и 'Заполнить',
    соответствующий текст и прикрепляя пустой шаблон выбранного файла к сообщению.

        Параметры:
            callback (CallbackQuery или Message): входящий callback запрос, ведущий в главное меню
            category (str): выбранный подраздел меню
            document_name (str): название выбранного файла

    '''

    # Создаём клавиатуру под выбранным файлом
    markup = await make_file_page_keyboard(category=category, document_name=document_name)

    # Загружаем буфер подгруженных документов и собираем полное имя файла,
    # который будет прикреплен к сообщению
    documents_buffer = await get_buffer_of_documents()
    document_name = f'{DIRECTORY_FOR_TEMPLATES}{document_name}.pdf'

    # FIX ME: сделать автоматическую подгрузку файлов перед началом работы бота в буфер
    # и убрать проверку на наличие файла в нём

    # Изменяем у сообщения, от которого поступил callback запрос, текст и клавиатуру на требуемые
    # и прикрепляем нужный файл вместо фотографии
    if document_name in documents_buffer:
        document = documents_buffer[document_name]
    else:
        document = types.FSInputFile(document_name, filename=document_name)

    if isinstance(callback, types.CallbackQuery):
        message = await bot.edit_message_media(chat_id=callback.message.chat.id,
                                               message_id=callback.message.message_id,
                                               media=InputMediaDocument(
                                                   media=document,
                                                   caption=FILE_PAGE_TEXT),
                                               reply_markup=markup)
    else:
        message = await bot.send_document(chat_id=callback.chat.id,
                                          document=document,
                                          caption=FILE_PAGE_TEXT,
                                          reply_markup=markup)

    if document_name not in documents_buffer:
        await update_document_buffer(document_name, message.document.file_id)

# ................................hendlers.................................#


@dp.callback_query(MenuCallbackData.filter())
async def navigate(callback: types.CallbackQuery, callback_data: MenuCallbackData):
    '''
    Функция, обрабатывающая callback запросы от инлайн клавиатуры меню и
    осуществляющая навигацию по этому меню

        Параметры:
            callback (CallbackQuery): принятый callback запрос, отправленный нажатой кнопкой меню
            callback_data (MenuCallbackData): данные, переданные с callback запросом

    '''

    # Создаём словарь соответствий уровня вложенности меню и функций-обработчиков страниц меню
    levels = {0: main_menu_proceccing,
              1: files_menu_proceccing,
              2: file_page_proceccing
              }

    # Выбираем нужную функцию обработчий по значению уровня вложенности. Уровень
    # получаем из соответствующего поля callback_data
    current_level_function = levels[callback_data.level]

    # Вызываем выбранную функцию-обработчик, передавая в неё соответствующие данные о разделе меню,
    # выбранном документе и уровне вложенности, которые хранятся в пришедшей callback_data
    await current_level_function(callback,
                                 category=callback_data.category,
                                 document_name=callback_data.document_name)

    # Отвечаем на callback запрос
    await callback.answer()


# Обработчик команды /start
@dp.message(CommandStart(), StateFilter(default_state))
async def start_command(messege: types.Message):
    # Отправляем краткое описание бота и загружаем главное меню в ответ на сообщение /start
    await messege.answer(text=DESCRIPTION)
    await main_menu_proceccing(messege)

# ..........................FSM..........................................#


@dp.callback_query(FillDocumentCallbackData.filter(), StateFilter(default_state))
async def fill_document(callback: types.CallbackQuery, callback_data: FillDocumentCallbackData, state: FSMContext):
    '''
    Функция входа в машину состояний. Активируется при callback запросе, содержащим FillDocumentCallbackData callback_data,
    отправляемую при нажатии на кнопку 'Заполнить документ'. Функция инициализирует хранилище для сбора данных, загружает
    последовательность токенов, соответствующую выбранному документу и запускает машину состояний, переводя её во второе
    состояние из этой цепочки.

        Параметры:
            callback (CallbackQuery): 
            callback_data (FillDocumentCallbackData):
            state (FSMContext):

    '''

    # Инициализируем словарь с даными пользователя, сохраняя туда информацию, которая потебуется
    # в дальнейшем для возврата в меню и заполнения выбранного зокумента и загружаем его в хранилище
    user_data = {'chain_of_states': CHAINS_OF_STATES[callback_data.document_name],
                 'document_name': callback_data.document_name,
                 'category': callback_data.category,
                 'id': callback.from_user.id,
                 'iteration': 0
                 }
    await state.update_data(user_data)

    # Устанавливаем следующее состояние для FSM -- первое в цепочке токенов
    next_state = user_data['chain_of_states'][0]

    # Удаляем клавиатуру меню и выводим сообщение с приглашением ввести первый токен из цепочки
    await callback.message.delete_reply_markup()
    await callback.message.answer(text=f'Введите {LEXICON[next_state]}')

    # Переводим машину состояний в промежуточное состояние -- состояние ввода данных
    await state.set_state(FSMFillPersonalData.middle_state)

    # Отвечаем на callback
    await callback.answer()


@dp.message(StateFilter(FSMFillPersonalData.middle_state))
async def process_name_sent(message: types.Message, state: FSMContext):
    '''
    Считывает введённые пользователем данные, просит ввести пользователя следующий токен
    и переводит FSN в следующее состояние.

        Параметры:
            message (types.Message): сообщение от пользователя, с введённым значением предыдущего токена
            state (FSMContext): данные FSM
    '''

    # Получаем данные пользователя из хранилища
    user_data = await state.get_data()

    # Записываем в словарь данных пользователя введённую пользователем информацию о текущем токене
    current_state = user_data['chain_of_states'][user_data['iteration']]
    user_data[current_state] = message.text

    # Достаём из цепочки токенов токен, следующий за текущим
    user_data['iteration'] += 1
    next_state = user_data['chain_of_states'][user_data['iteration']]

    # Обновляем данные в хранилище и выводим сообщение с приглашением ввести следующий токен
    await state.update_data(user_data)
    await message.answer(text=f'Введите {LEXICON[next_state]}')

    # Переводим FSM в следующее состояние, конечное (если цепочка закончилась)
    # или ввода токенов (если она продолжается)
    await state.set_state(FSMFillPersonalData.final_state if next_state == 'final_state'
                          else FSMFillPersonalData.middle_state)


@dp.message(StateFilter(FSMFillPersonalData.final_state))
async def process_final_state_sent(message: types.Message, state: FSMContext):
    '''
    Обрабатывает финальное состояние FSM. Создаёт и отправляет пользователю документ, 
    заполненный его данными и возвращает его в меню документов. Выходит из FSM, 
    переводя её в состояние по умолчанию.

        Параметры:
            message (types.Message): сообщение от пользователя, с введённым значением токена -- желаемого имени файла
            state (FSMContext): данные FSM
    '''

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

    message = await bot.send_photo(chat_id=message.chat.id,
                                   photo=photo,
                                   caption=LEXICON['wait'])

    if photo_name not in photo_buffer:
        await update_photo_buffer(photo_name, message.photo[-1].file_id)

    await fill_template(user_data=user_data, document_name=user_data['document_name'])

    # Cобираем полное имя pdf файла, сгенерированного функцией fill_template
    document_name = f'{DIRECTORY_FOR_LATEX_FILES}file_for_user{user_data["id"]}.pdf'

    # Отправляем пользователю сообщение с прикреплённым к нему заполненным файлом
    # При этом меняем его название на то, которое было введено пользователем
    await bot.send_document(chat_id=message.chat.id,
                            document=types.FSInputFile(
                                document_name,
                                filename=f'{filename}.pdf'),
                            caption=WITH_FILL_FILE_MESSAGE)

    # Удаляем отправленный файл с компьютера, чтобы не засорять директорию
    if os.path.isfile(document_name):
        os.unlink(document_name)

    # Возвращаем пользователя на страницу меню файла, который был заполнен
    await file_page_proceccing(message,
                               category=user_data['category'],
                               document_name=user_data['document_name'])

    # Очишаем машину состояний (выходим из неё в состояние по умолчанию)
    await state.clear()


# Съедаем весь спам, не являющийся поддерживаемыми командами
@dp.message()
async def delete_spam(message: types.Message):
    await message.delete()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
