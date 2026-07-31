import os
import json
import requests
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)
# Секретный ключ сессии Flask (для хранения выбранного языка).
# В проде задаётся переменной окружения SECRET_KEY, локально — запасное значение.
app.secret_key = os.environ.get("SECRET_KEY", "wedding_secret_key_123")

DATA_FILE = os.path.join(os.path.dirname(__file__), "responses.json")

# ------------------------------------------------------------------
#  ТЕЛЕГРАМ-УВЕДОМЛЕНИЯ
#  ВАЖНО: токен и chat_id больше НЕ хранятся в коде.
#  Задайте их как переменные окружения (см. README) —
#  иначе бот-токен утечёт в публичный репозиторий на GitHub.
# ------------------------------------------------------------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_IDS = [
    int(cid) for cid in os.environ.get("TELEGRAM_CHAT_IDS", "").split(",") if cid.strip()
]

# ------------------------------------------------------------------
#  ТЕКСТЫ И ПЕРЕВОДЫ (RU / UZ)
# ------------------------------------------------------------------
TRANSLATIONS = {
    "ru": {
        "groom": "Диёрбек",
        "bride": "Мукаддас",
        "date_human_day": "11",
        "date_human_month": "Сентябрь",
        "date_human_year": "2026",
        "date_human_weekday": "Пятница",
        "city": "Нукус, Каракалпакстан",
        "invitation_text": (
            "В этот радостный день, когда соединяются наши сердца, мы хотим "
            "разделить самые дорогие мгновения жизни с самыми близкими "
            "и любимыми людьми. Будем счастливы видеть вас на нашем торжестве."
        ),
        "where": "Где",
        "address_title": "Адрес",
        "venue_name": "Ресторан «Grand Shadel»",
        "venue_address": "Нукус, ул. Аллаяра Досназарова, 234/9",
        "map_btn": "Смотреть на карте",
        "countdown_title": "До торжества",
        "countdown_subtitle": "Ждём",
        "days": "Дней",
        "hours": "Часов",
        "minutes": "Минут",
        "seconds": "Секунд",
        "rsvp_title": "Присутствие",
        "name_placeholder": "Ваше имя и фамилия",
        "attending_yes": "Я приду",
        "attending_no": "К сожалению, не смогу",
        "guests_label": "Количество гостей",
        "wish_placeholder": "Ваши пожелания...",
        "send_btn": "Отправить ответ",
    },
    "uz": {
        "groom": "Diyorbek",
        "bride": "Muqaddas",
        "date_human_day": "11",
        "date_human_month": "Sentabr",
        "date_human_year": "2026",
        "date_human_weekday": "Juma",
        "city": "Nukus, Qoraqalpog'iston",
        "invitation_text": (
            "Qalblarimiz tutashayotgan ushbu quvonchli kunda, hayotimizning eng "
            "qadrli damlarini siz kabi yaqin va qadrli insonlarimiz bilan baham ko'rmoqchimiz. "
            "Tantanalarimizda sizni ko'rishdan mamnun bo'lamiz."
        ),
        "where": "Qayerda",
        "address_title": "Manzil",
        "venue_name": "«Grand Shadel» restorani",
        "venue_address": "Nukus shahri, Allayar Dosnazarov ko'chasi, 234/9",
        "map_btn": "Xaritada ko'rish",
        "countdown_title": "Tantanagacha",
        "countdown_subtitle": "Kutmoqdamiz",
        "days": "Kun",
        "hours": "Soat",
        "minutes": "Daqiqa",
        "seconds": "Soniya",
        "rsvp_title": "Tashrif buyurish",
        "name_placeholder": "Ism va familiyangiz",
        "attending_yes": "Tashrif buyuraman",
        "attending_no": "Afsuski, borolmayman",
        "guests_label": "Mehmonlar soni",
        "wish_placeholder": "Ezgu tilaklaringiz...",
        "send_btn": "Javobni yuborish",
    },
}

EVENT = {
    "date_iso": "2026-09-11T18:00:00",
    "map_url": "https://yandex.uz/maps/-/CTvQMQ~r",
}

# ------------------------------------------------------------------
#  ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------------------------------------------
def load_responses():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def is_duplicate(new_entry):
    responses = load_responses()
    if not responses:
        return False
    last = responses[-1]
    return (
        last.get("name") == new_entry["name"]
        and last.get("attending") == new_entry["attending"]
        and last.get("wish") == new_entry["wish"]
    )


def save_response(entry):
    responses = load_responses()
    responses.append(entry)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)


def send_to_telegram(data):
    if not BOT_TOKEN or not CHAT_IDS:
        # Токен/чаты не настроены — просто пропускаем уведомление.
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    status = "✅ Придёт" if data["attending"] == "yes" else "❌ К сожалению, не сможет"
    wish_text = data["wish"] if data["wish"] else "Без пожеланий"

    text = (
        "💍 *Новый ответ на приглашение!*\n\n"
        f"👤 *Имя:* {data['name']}\n"
        f"📊 *Статус:* {status}\n"
        f"👥 *Количество гостей:* {data['guests']}\n"
        f"💌 *Пожелание:* {wish_text}"
    )

    for chat_id in CHAT_IDS:
        try:
            requests.post(
                url,
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=5,
            )
        except Exception as e:
            print(f"Ошибка отправки: {e}")


# ------------------------------------------------------------------
#  МАРШРУТЫ И ПЕРЕКЛЮЧЕНИЕ ЯЗЫКА
# ------------------------------------------------------------------
@app.route("/lang/<lang_code>")
def set_language(lang_code):
    """Маршрут для смены языка"""
    if lang_code in TRANSLATIONS:
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("index"))


@app.route("/")
def index():
    lang = session.get("lang", "ru")
    t = TRANSLATIONS[lang]
    return render_template("index.html", event=EVENT, t=t, current_lang=lang)


@app.route("/rsvp", methods=["POST"])
def rsvp():
    data = request.get_json(force=True) or {}
    name = (data.get("name") or "").strip()
    attending = data.get("attending")
    guests = data.get("guests") or 1
    wish = (data.get("wish") or "").strip()

    if not name or attending not in ("yes", "no"):
        return jsonify({"ok": False, "error": "Заполните имя / Ismingizni kiriting."}), 400

    entry = {
        "name": name,
        "attending": attending,
        "guests": guests,
        "wish": wish,
        "received_at": datetime.now().isoformat(timespec="seconds"),
    }

    if is_duplicate(entry):
        return jsonify({"ok": True, "message": "Уже сохранено"})

    save_response(entry)
    send_to_telegram(entry)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True)
