from .fill_document import fsm_router
from .menu_handlers import menu_router
from .user import user_router

routers_list = [menu_router, fsm_router, user_router]

__all__ = ['routers_list']