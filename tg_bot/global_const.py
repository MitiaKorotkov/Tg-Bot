DESCRIPTION = '''Описание этого бота и его команд'''
MAIN_MENU_TEXT = '''Вот такие группы заявлений у меня есть'''
FILES_MENU_TEXT = '''В данном разделе есть следующие файлы'''
FILE_PAGE_TEXT = '''Вот пустой бланк. Можете заполнить его сами или попросить об этом меня'''
WITH_FILL_FILE_MESSAGE = '''Вот ваш заполненный файл'''

DIRECTORY_FOR_LATEX_FILES = 'database/tmp_latex_files/'
DIRECTORY_FOR_TEMPLATES = 'database/templates/'
DIRECTORY_FOR_PHOTOS = 'database/photos/'

MAIN_MENU_PHOTO = 'main_menu_photo.png'
FILES_MENU_PHOTO = 'main_menu_photo.jpg'
DOWNLOAD_PHOTO = 'submenu_photo.jpg'

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
           'wait': 'Пожалуйста, подождите немного, документ заполняется',
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
