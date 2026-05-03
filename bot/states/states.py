"""
FSM (Finite State Machine) holatlari — barcha ekranlar uchun.
"""
from aiogram.fsm.state import State, StatesGroup


# ─── SENDER STATES (Jo'natuvchi yo'li) ───────
class SenderRegistration(StatesGroup):
    """S-10..S-13: Ro'yxatdan o'tish"""
    fullname = State()      # S-10
    phone = State()         # S-11
    location = State()      # S-12
    select_month = State()  # S-13


class SenderSearch(StatesGroup):
    """S-14..S-17: Kuryer qidirish va so'rov"""
    viewing_couriers = State()  # S-14
    courier_detail = State()    # S-15
    confirm_request = State()   # S-16


# ─── COURIER STATES (Kuryer yo'li) ───────────
class CourierRegistration(StatesGroup):
    """S-20..S-27: Kuryer ro'yxatdan o'tish"""
    fullname = State()       # S-20
    phone = State()          # S-21
    location = State()       # S-22
    departure_city = State() # S-23
    flight_date = State()    # S-23
    flight_time = State()    # S-23
    max_kg = State()         # S-24
    price_per_kg = State()   # S-24
    restrictions = State()   # S-25
    custom_restriction = State()
    video = State()          # S-26


# ─── DEAL STATES (Kelishuv jarayoni) ─────────
class DealStates(StatesGroup):
    """S-30..S-35"""
    chatting = State()      # S-31: Bot ichida chat
    rating = State()        # S-35: Baho berish


# ─── COMPLAINT STATES ─────────────────────────
class ComplaintStates(StatesGroup):
    """S-52"""
    select_reason = State()
    enter_detail = State()


# ─── ADMIN STATES ─────────────────────────────
class AdminStates(StatesGroup):
    """A-01..A-06"""
    reviewing_video = State()    # A-02
    reject_reason = State()      # A-02: Rad sababi
    viewing_complaint = State()  # A-03
    broadcast_target = State()   # A-06
    broadcast_text = State()     # A-06
    taxi_add_driver = State()
    taxi_add_countries = State()
    taxi_add_cargo = State()
    taxi_add_capacity = State()
    taxi_add_desc = State()
    taxi_edit_value = State()
    listing_edit_value = State()
