from aiogram.fsm.state import StatesGroup, State


class FSMFillPersonalData(StatesGroup):
    '''
    Это класс с состояниями машины состояний.

    middle_state: состояние ввода персональных данных
    final_state: состояние выхода из машины состояний
    '''
    middle_state = State()
    final_state = State()
