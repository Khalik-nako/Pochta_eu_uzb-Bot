"""
O'zbek tili xabarlari — sof o'zbek, ruscha so'zsiz.
"""

# ─── START ───────────────────────────────────
START_WELCOME = """Assalomu alaykum! 👋

Tilni tanlang:"""

START_RETURNING = "Xush kelibsiz qaytib! 🎉"

# ─── ONBOARDING ──────────────────────────────
SELECT_COUNTRY = "Qaysi davlatdasiz? 🌍"

LEGAL_TEXT = """Xush kelibsiz! 🎉

Bu bot Yevropadan O'zbekistonga pochta yetkazishda \
jo'natuvchilar va kuryerlarni birlashtiradi.

⚠️ <b>Muhim:</b> Bot faqat vositachi. \
To'lov va yuk masalasi to'liq \
foydalanuvchilar o'rtasida hal qilinadi.

Davom etish uchun quyidagini tasdiqlang:"""

LEGAL_ACCEPTED = "✅ Rahmat! Davom etamiz."

# ─── MAIN MENU ───────────────────────────────
MAIN_MENU = "Nima qilmoqchisiz? 👇"

# ─── SENDER FLOW ─────────────────────────────
ENTER_FULLNAME = """Ismingiz va familyangizni kiriting:

<i>Masalan: Bobur Toshmatov</i>"""

ENTER_PHONE = """Telefon raqamingizni kiriting:

<i>Masalan: +371 2345 6789</i>"""

PHONE_ALREADY_EXISTS = """⚠️ Bu raqam allaqachon ro'yxatdan o'tgan.

Agar bu sizning raqamingiz bo'lsa, admin bilan bog'laning."""

SEND_LOCATION = """Joylashuvingizni yuboring 📍

Bu kuryer sizga yaqinroq bo'lsin uchun kerak."""

SELECT_MONTH = "Qachon jo'natmoqchisiz? 📅"

COURIERS_FOUND = "✅ Mos kuryrlar topildi! Saralash:"

NO_COURIERS = """Bu oyda bu yo'nalishda kuryer yo'q 😔

Yangi kuryer qo'shilganda xabar beraymi?"""

SUBSCRIBED_NOTIFY = "🔔 Yangi kuryer qo'shilganda xabar beramiz!"

SORT_BY_DATE = "⚡ Eng yaqin sana"
SORT_BY_PRICE = "💰 Eng arzon"
SORT_BY_RATING = "⭐ Eng yuqori reyting"

# ─── COURIER CARD ────────────────────────────
def courier_card(name: str, city: str, date: str, time: str,
                 max_kg: float, price: float, rating: float,
                 deal_count: int, restrictions: str) -> str:
    return (
        f"<b>{name}</b> — {city} → Toshkent\n"
        f"📅 {date} · {time}\n"
        f"⚖️ Max: {max_kg} kg · 💶 €{price}/kg\n"
        f"⭐ {rating} ({deal_count} ta deal)\n"
        f"🚫 Olmaydi: {restrictions or 'koʼrsatilmagan'}"
    )

# ─── SCAM WARNING ────────────────────────────
SCAM_WARNING = """⚠️ <b>Jo'natishdan oldin o'qing:</b>

— Oldindan pul o'tkazmang
— To'lov faqat yuk yetgandan keyin
— Bot tashqarisida kelishmang
— Muammo bo'lsa adminga yozing"""

REQUEST_SENT = """✅ So'rovingiz yuborildi!

{courier_name} javob berganda sizga xabar beramiz 🔔

{city} → Toshkent · {date}"""

# ─── COURIER FLOW ────────────────────────────
ENTER_FLIGHT_DATE = """Reysning aniq sanasini kiriting:

<i>Masalan: 15.05.2026</i>
(kun.oy.yil formatida)"""

DATE_FORMAT_ERROR = "Sana biroz noto'g'ri chiqdi 😊 Shunday yozing: 15.05.2026 — va davom etamiz!"

ENTER_FLIGHT_TIME = """Uchish vaqtini kiriting:

<i>Masalan: 09:30</i>
(sizning davlatingiz vaqti bo'yicha)"""

TIME_FORMAT_ERROR = "Vaqt ham shu formatda bo'lishi kerak: 09:30 😊"

ENTER_MAX_KG = """Necha kg yuk olasiz?

<i>Masalan: 8</i>"""

ENTER_PRICE = """Narxingiz necha €/kg?

<i>Masalan: 8</i>"""

SELECT_RESTRICTIONS = "Qabul qilmaydigan narsalar:\n(birnechtasini tanlash mumkin)"

ENTER_CUSTOM_RESTRICTION = "Qabul qilmaydigan narsani yozing:"

SEND_VERIFICATION_VIDEO = """🎥 <b>Tasdiqlash videosini yuboring!</b>

Videoda ko'rsating:
✅ Yuzingiz aniq ko'rinsin
✅ Pasportingizni ushlab turing
✅ "Men [ism], [sana]da Toshkentga uchaman" — deb ayting

🔒 Video faqat admin tomonidan ko'riladi.
Yuk yetkazilgandan keyin video o'chirib tashlanadi.
⚠️ Aldov holatida video politsiyaga taqdim etilishi mumkin."""

VIDEO_SENT_WAITING = """✅ Videongiz adminga yuborildi!

⏳ Tasdiqlash: 2–12 soat

Natija haqida sizga xabar beriladi 🔔"""

VIDEO_REJECTED = """😔 Afsuski, videongiz tasdiqlanmadi.

<b>Sabab:</b> {reason}

Iltimos, qayta video yuboring."""

LISTING_PUBLISHED = """🎉 <b>Tabriklaymiz! E'loningiz joylashdi!</b>

{city} → Toshkent
📅 {date} · {time}
⚖️ {max_kg} kg · 💶 €{price}/kg

⚠️ <b>Eslatma:</b>
— To'lov faqat yuk yetkazilgandan keyin
— Oldindan pul so'ramang — bu scam hisoblanadi
— Muammo bo'lsa adminga yozing"""

AGE_RESTRICTED = """Salom! 👋 Pasportingizga ko'ra siz hali 18 yoshga to'lmagan ko'rinasiz.

Xizmatimizdan foydalanish uchun 18 yoshdan katta bo'lish kerak.

Agar bu xato bo'lsa, admin bilan bog'laning 😊"""

# ─── DEAL FLOW ───────────────────────────────
NEW_REQUEST_FOR_COURIER = """📬 <b>Yangi so'rov!</b>

👤 Kim: {sender_name}
📍 Joylashuv: {location}
💬 Izoh: {note}"""

REQUEST_ACCEPTED = "🎉 Kuryer so'rovingizni qabul qildi!"
REQUEST_REJECTED = "😔 Kuryer so'rovingizni qabul qilmadi."

DEAL_CHAT_INTRO = """💬 <b>Kelishuv boshlandi!</b>

Quyidagilarni muhokama qiling:
📍 Yukni qayerdan va qanday oladi?
🕐 Qaysi kuni, soatda uchrashiladi?
📦 Yukni qanday o'rash kerak?

Hammasi kelishilgandan so'ng — <b>"Kelishdim"</b> tugmasini bosing."""

DEAL_CONFIRMED = """✅ <b>Deal tasdiqlandi!</b>

{city} → Toshkent · {date} · {time}

Reysga 1 kun qolganda kuryer kontakt ma'lumotlari yuboriladi 🔔"""

USERNAME_SHARE_SENDER = """✈️ <b>Ertaga reys!</b>

Kuryer ma'lumoti:
{username}

To'g'ridan-to'g'ri bog'laning, yukni topshiring.
⚠️ To'lovni faqat yuk olgandan so'ng qiling! 💰"""

USERNAME_SHARE_COURIER = """✈️ <b>Ertaga reys!</b>

Jo'natuvchi ma'lumoti:
{username}

To'g'ridan-to'g'ri bog'laning, yukni oling."""

CONFIRM_DELIVERY_COURIER = "Yukni yetkazdingizmi? ✅"

CONFIRM_DELIVERY_SENDER = """📦 Pochtangiz yetib keldimi?

Tasdiqlashdan so'ng deal yakunlanadi."""

DEAL_COMPLETED = """🎉 <b>Deal yakunlandi!</b>

Iltimos, baho bering:"""

# ─── PROFILE ─────────────────────────────────
MY_LISTINGS_TITLE = "📋 Sizning e'lonlaringiz:"
MY_RATING = "⭐ Sizning reytingiz: {rating}/5\nJami deallar: {count}"
SETTINGS_TITLE = "⚙️ Sozlamalar"

# ─── COMPLAINT ───────────────────────────────
COMPLAINT_REASON = "Shikoyat sababi:"
COMPLAINT_DETAIL = "Batafsil yozing:"
COMPLAINT_SENT = "📨 Shikoyatingiz adminga yuborildi. Ko'rib chiqamiz!"

# ─── HELP ────────────────────────────────────
HELP_TEXT = """❓ <b>Yordam</b>

Ko'p so'raladigan savollar:

❓ <b>Kuryer qanday tanlanadi?</b>
Oy tanlaysiz → mos kuryrlar ro'yxati chiqadi → bittasini tanlab so'rov yuborasiz.

❓ <b>To'lov qachon qilinadi?</b>
Faqat yuk O'zbekistonga yetib kelgandan keyin. Oldindan to'lamang!

❓ <b>Username qachon beriladi?</b>
Reysga 1 kun qolganda ikki tomon bir-birining kontaktini oladi.

❓ <b>Scamdan qanday himoyalanish?</b>
Bot tashqarisida kelishmang. Muammo bo'lsa adminga yozing."""

# ─── ERRORS ──────────────────────────────────
ERROR_GENERAL = "Xatolik yuz berdi 😔 Iltimos, qaytadan urinib ko'ring."
ERROR_BACK = "⬅️ Orqaga"
BACK_TO_MENU = "🏠 Bosh menyu"

# ─── COURIER FLOW (qo'shimcha) ───────────────
ENTER_MAX_KG = """Necha kg yuk olasiz?

<i>Masalan: 8</i>"""

ENTER_PRICE = """Narxingiz necha €/kg?

<i>Masalan: 8</i>"""

TIME_FORMAT_ERROR = "Vaqt biroz noto'g'ri chiqdi 😊 Shunday yozing: 09:30 — va davom etamiz!"

SELECT_RESTRICTIONS = """Qanday narsalarni <b>olmaysiz</b>? (ixtiyoriy)

Tegishlilarini belgilang, so'ng «Davom etish» tugmasini bosing 👇"""

SEND_VERIFICATION_VIDEO = """🎥 <b>Tasdiqlash videosini yuboring!</b>

Videoda ko'rsating:
✅ Yuzingiz aniq ko'rinsin
✅ Pasportingizni ushlab turing
✅ «Men [ism], [sana]da Toshkentga uchaman» — deb ayting

🔒 Video faqat admin tomonidan ko'riladi.
Yuk yetkazilgandan keyin video o'chirib tashlanadi.

⚠️ Aldov holatida video politsiyaga taqdim etilishi mumkin.

📹 <b>Video yoki video xabar (doiracha) yuboring!</b>"""

VIDEO_SENT_WAITING = """✅ <b>Videongiz adminga yuborildi!</b>

⏳ Tasdiqlash: 2–12 soat
Natija haqida sizga xabar beriladi 🔔"""

# ─── COMPLAINT ───────────────────────────────
COMPLAINT_REASON = """🚨 <b>Shikoyat</b>

Shikoyat sababini tanlang:"""

COMPLAINT_DETAIL = """Muammoni batafsil yozing:

<i>Masalan: Kuryerim meni e'tiborsiz qoldirdi, telefonga javob bermadi</i>"""

COMPLAINT_SENT = """✅ <b>Shikoyatingiz qabul qilindi!</b>

Admin 24 soat ichida ko'rib chiqadi va siz bilan bog'lanadi 🔔"""

# ─── AGE RESTRICTED ──────────────────────────
AGE_RESTRICTED = """⛔ <b>Ro'yxatdan o'tish mumkin emas</b>

Bu bot faqat 18 yoshdan katta foydalanuvchilar uchun.

Savollar bo'lsa admin bilan bog'laning."""

# ─── HELP ────────────────────────────────────
HELP_TEXT = """❓ <b>Yordam</b>

<b>Bu bot nima?</b>
Yevropadan O'zbekistonga pochta yetkazishda jo'natuvchilar va kuryerlarni birlashtiradi.

<b>Qanday ishlaydi?</b>
1️⃣ Jo'natuvchi kuryer qidiradi va so'rov yuboradi
2️⃣ Kuryer so'rovni qabul qiladi
3️⃣ Kelishasizlar va yuk topshiriladi
4️⃣ Yuk yetgandan keyin to'lov amalga oshiriladi

<b>Muhim qoidalar:</b>
⚠️ Oldindan pul o'tkazmang
⚠️ To'lov faqat yuk yetgandan keyin
⚠️ Bot tashqarisida kelishmang

📞 Muammo bo'lsa adminga yozing"""
