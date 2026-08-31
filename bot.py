import json
import os
import time
from datetime import date
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TRAVEL_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

PRICE_LIMIT = int(os.getenv("PRICE_LIMIT", "25000"))
CHECK_MINUTES = int(os.getenv("CHECK_MINUTES", "15"))

DESTINATION = "CXR"

ORIGINS = {
    "SVX": "Екатеринбург",
    "MOW": "Москва",
    "KZN": "Казань",
    "UFA": "Уфа",
    "KUF": "Самара",
}

STATE_FILE = Path("seen_prices.json")


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


def load_state():
    if not STATE_FILE.exists():
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(
            state,
            file,
            ensure_ascii=False,
            indent=2,
        )


def search_city(origin):
    url = (
        "https://api.travelpayouts.com/"
        "aviasales/v3/search_by_price_range"
    )

    params = {
        "origin": origin,
        "destination": DESTINATION,
        "value_min": 1,
        "value_max": 40000,
        "one_way": "true",
        "direct": "false",
        "locale": "ru",
        "currency": "rub",
        "market": "ru",
        "limit": 100,
        "page": 1,
        "token": TRAVEL_TOKEN,
    }

    response = requests.get(
        url,
        params=params,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("success"):
        return []

    return data.get("data", [])


def check_ticket(origin, ticket, state):
    price = ticket.get("price")
    departure = ticket.get("departure_at")
    transfers = ticket.get("transfers")

    if price is None or departure is None:
        return

    try:
        departure_date = date.fromisoformat(
            departure[:10]
        )
    except ValueError:
        return

    if departure_date < date.today():
        return

    if price > PRICE_LIMIT:
        return

    city = ORIGINS[origin]

    key = (
        f"{origin}-"
        f"{departure_date}-"
        f"{transfers}"
    )

    old_price = state.get(key)

    if old_price is not None and price >= old_price:
        return

    state[key] = price

    if transfers == 0:
        transfer_text = "ПРЯМОЙ РЕЙС 🔥"
    elif transfers == 1:
        transfer_text = "1 пересадка"
    else:
        transfer_text = f"{transfers} пересадки"

    priority = ""

    if origin == "SVX" and transfers == 0:
        priority = (
            "\n\n🔥🔥🔥 ПРИОРИТЕТ!"
            "\nПрямой Екатеринбург → Нячанг"
        )

    price_text = f"{price:,}".replace(",", " ")
    limit_text = f"{PRICE_LIMIT:,}".replace(",", " ")

    message = (
        "✈️ НАЙДЕН ДЕШЁВЫЙ БИЛЕТ!\n\n"
        f"📍 {city} → Нячанг\n"
        f"💰 {price_text} ₽\n"
        f"📅 {departure_date.strftime('%d.%m.%Y')}\n"
        f"🔄 {transfer_text}"
        f"{priority}\n\n"
        f"⚡ Цена ниже установленного порога "
        f"{limit_text} ₽"
    )

    send_telegram(message)

    print(
        "ALERT:",
        city,
        departure_date,
        price,
        transfers,
    )


def check_all():
    state = load_state()

    print()
    print("=" * 55)
    print("Проверяем авиабилеты...")
    print("=" * 55)

    for origin, city in ORIGINS.items():
        try:
            tickets = search_city(origin)

            future_tickets = []

            for ticket in tickets:
                departure = ticket.get("departure_at")

                if not departure:
                 continue

                try:
                    departure_date = date.fromisoformat(
                        departure[:10]
                    )
                except ValueError:
                    continue

                if departure_date >= date.today():
                    future_tickets.append(ticket)

            if future_tickets:
                cheapest = min(
                    future_tickets,
                    key=lambda item: item.get(
                        "price",
                        999999999,
                    ),
                )

                print(
                    city,
                    "→ CXR | минимум:",
                    cheapest.get("price"),
                    "₽ |",
                    cheapest.get("departure_at"),
                    "| пересадок:",
                    cheapest.get("transfers"),
                )

            else:
                print(
                    city,
                    "→ CXR | вариантов до 40 000 ₽ нет",
                )

            for ticket in future_tickets:
                check_ticket(
                    origin,
                    ticket,
                    state,
                )

        except Exception as error:
            print(
                f"Ошибка при проверке {city}:",
                error,
            )

        time.sleep(2)

    save_state(state)

    print("=" * 55)
    print(
        f"Проверка завершена. "
        f"Следующая через {CHECK_MINUTES} мин."
    )


if __name__ == "__main__":
send_telegram("✅ ТЕСТ: уведомления работают")
    

    check_all()
