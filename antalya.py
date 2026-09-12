import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TRAVEL_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

DESTINATION = "AYT"
PRICE_LIMIT = 7000

DATE_FROM = "2026-09-19"
DATE_TO = "2026-09-23"

ORIGINS = {
    "PEE": "Пермь",
    "SVX": "Екатеринбург",
}


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    targets = [CHAT_ID, TELEGRAM_CHANNEL_ID]

    for chat_id in targets:
        if not chat_id:
            continue

        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
            },
            timeout=60,
        )

        response.raise_for_status()


def search_city(origin, city):
    url = "https://api.travelpayouts.com/aviasales/v3/search_by_price_range"

    params = {
        "origin": origin,
        "destination": DESTINATION,
        "value_min": 1,
        "value_max": 20000,
        "one_way": "true",
        "direct": "true",
        "locale": "ru",
        "currency": "rub",
        "market": "ru",
        "limit": 30,
        "page": 1,
        "token": TRAVEL_TOKEN,
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    data = response.json().get("data", [])

    suitable = []

    for ticket in data:
        departure = ticket.get("departure_at", "")[:10]
        price = ticket.get("price")
        transfers = ticket.get("transfers")

        if not departure:
            continue

        if departure < DATE_FROM or departure > DATE_TO:
            continue

        if transfers != 0:
            continue

        if price is None or price > PRICE_LIMIT:
            continue

        suitable.append(ticket)

    if not suitable:
        print(
            f"{city} → Анталья: прямых вариантов "
            f"{DATE_FROM}–{DATE_TO} до 7 000 ₽ нет"
        )
        return

    suitable.sort(key=lambda x: x.get("price", 999999))

    for ticket in suitable[:5]:
        price = ticket.get("price")
        departure = ticket.get("departure_at", "")[:10]

        text = (
            "🔥 ДЕШЁВЫЙ ПРЯМОЙ РЕЙС 🔥\n\n"
            f"{city} → Анталья\n"
            f"Цена: {price:,} ₽\n"
            f"Дата: {departure}\n"
            "Пересадок: 0"
        ).replace(",", " ")

        send_telegram(text)

        print(
            f"Найден билет: {city} → Анталья | "
            f"{price} ₽ | {departure} | прямой"
        )


def search_flights():
    for origin, city in ORIGINS.items():
        search_city(origin, city)


if __name__ == "__main__":
    search_flights()
