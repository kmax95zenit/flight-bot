import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TRAVEL_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

DESTINATION = "AYT"

DATE_FROM = "2026-09-19"
DATE_TO = "2026-09-23"

ORIGINS = {
    "PEE": {
        "city": "Пермь",
        "price_limit_per_person": 12500,
        "price_limit_for_two": 25000,
    },
    "SVX": {
        "city": "Екатеринбург",
        "price_limit_per_person": 10000,
        "price_limit_for_two": 20000,
    },
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


def search_city(origin, city, price_limit_per_person, price_limit_for_two):
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

        if price is None or price > price_limit_per_person:
            continue

        suitable.append(ticket)

    if not suitable:
        print(
            f"{city} → Анталья: прямых вариантов "
            f"{DATE_FROM}–{DATE_TO} до {price_limit_for_two:,} ₽ на двоих нет"
        )
        return

    suitable.sort(key=lambda x: x.get("price", 999999))

    for ticket in suitable[:5]:
        price_per_person = ticket.get("price")
        total_price = price_per_person * 2
        departure = ticket.get("departure_at", "")[:10]

        text = (
            "🔥 ДЕШЁВЫЙ ПРЯМОЙ РЕЙС 🔥\n\n"
            f"{city} → Анталья\n"
            f"Цена за 1: {price_per_person:,} ₽\n"
            f"Цена за 2: {total_price:,} ₽\n"
            f"Дата: {departure}\n"
            "Пересадок: 0"
        ).replace(",", " ")

        send_telegram(text)

        print(
            f"Найден билет: {city} → Анталья | "
            f"{price_per_person} ₽ за 1 | "
            f"{total_price} ₽ за 2 | "
            f"{departure} | прямой"
        )


def search_flights():
    for origin, settings in ORIGINS.items():
        search_city(
            origin,
            settings["city"],
            settings["price_limit_per_person"],
            settings["price_limit_for_two"],
        )


if __name__ == "__main__":
    search_flights()
