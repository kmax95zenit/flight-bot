import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
TRAVEL_TOKEN = os.getenv("TRAVELPAYOUTS_TOKEN")

PRICE_LIMIT = 10000

DATE_FROM = "2026-10-02"
DATE_TO = "2026-10-06"

TURKEY_AIRPORTS = {
    "GZP": "Аланья / Газипаша",
    "AYT": "Анталья",
    "DLM": "Даламан",
    "BJV": "Бодрум",
    "ADB": "Измир",
}

RUSSIA_AIRPORTS = {
    "PEE": "Пермь",
    "SVX": "Екатеринбург",
    "CEK": "Челябинск",
    "UFA": "Уфа",
    "KZN": "Казань",
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


def search_route(origin, origin_name, destination, destination_name):
    url = "https://api.travelpayouts.com/aviasales/v3/search_by_price_range"

    params = {
        "origin": origin,
        "destination": destination,
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

        suitable.append(
            {
                "origin": origin,
                "origin_name": origin_name,
                "destination": destination,
                "destination_name": destination_name,
                "departure": departure,
                "price": price,
            }
        )

    return suitable


def search_flights():
    all_found = []

    for origin, origin_name in TURKEY_AIRPORTS.items():
        for destination, destination_name in RUSSIA_AIRPORTS.items():
            print(
                f"Проверяю: {origin_name} → {destination_name}"
            )

            try:
                found = search_route(
                    origin,
                    origin_name,
                    destination,
                    destination_name,
                )

                all_found.extend(found)

            except Exception as e:
                print(
                    f"Ошибка маршрута "
                    f"{origin_name} → {destination_name}: {e}"
                )

    if not all_found:
        print(
            f"Прямых билетов до {PRICE_LIMIT:,} ₽ "
            f"на даты {DATE_FROM}–{DATE_TO} не найдено"
        )
        return

    all_found.sort(key=lambda x: x["price"])

    top_results = all_found[:10]

    for ticket in top_results:
        text = (
            "🔥 ДЕШЁВЫЙ ПРЯМОЙ РЕЙС ИЗ ТУРЦИИ 🔥\n\n"
            f"{ticket['origin_name']} → {ticket['destination_name']}\n"
            f"Цена: {ticket['price']:,} ₽\n"
            f"Дата: {ticket['departure']}\n"
            "Пересадок: 0"
        ).replace(",", " ")

        send_telegram(text)

        print(
            f"Найден билет: "
            f"{ticket['origin_name']} → "
            f"{ticket['destination_name']} | "
            f"{ticket['price']} ₽ | "
            f"{ticket['departure']}"
        )


if __name__ == "__main__":
    search_flights()
