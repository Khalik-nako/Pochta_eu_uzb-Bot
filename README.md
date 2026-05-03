# Pochta Bot

A Telegram bot connecting parcel senders with couriers flying between Europe and Uzbekistan. Built with aiogram 3.x, SQLite, and async Python.

---

## What it does

- **Senders** register, browse available couriers by month, and send delivery requests
- **Couriers** post listings with flight info, upload a verification video, and accept/reject requests
- **Admins** review video submissions, handle complaints, and broadcast messages
- Supports Uzbek 🇺🇿 and Russian 🇷🇺 languages throughout
- Bot-mediated chat between sender and courier before they exchange contacts

- On first `/start`, new users go through: language → country → legal consent → main menu
- Courier listings require admin approval before becoming visible
- Bot-mediated chat allows senders and couriers to communicate without sharing contacts before the flight
- All times are stored in UTC; displayed in the user's country timezone