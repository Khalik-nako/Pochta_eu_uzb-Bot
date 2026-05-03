from aiogram import Router

from .start import router as start_router
from .sender import router as sender_router
from .courier import router as courier_router
from .deal import router as deal_router
from .profile import router as profile_router
from .admin import router as admin_router
from .taxi import router as taxi_router

main_router = Router(name="main")

# Router include order determines handler priority.
# FSM-based routers (sender, courier, deal, taxi) MUST come before start_router
# because start_router has a catch-all @router.message() at the bottom that
# would swallow all text messages otherwise — even in the middle of FSM flows.
# Admin router first because it has an AdminFilter that rejects non-admins fast.
main_router.include_routers(
    admin_router,
    sender_router,
    courier_router,
    deal_router,
    taxi_router,
    profile_router,
    start_router,
)

__all__ = ["main_router"]
