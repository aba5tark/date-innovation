import io
import os
import requests
import qrcode
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


@app.get("/")
def index():
    # Build a QR code for this exact public URL, so it works after deployment.
    public_url = request.url_root.rstrip("/") + "/"
    qr = qrcode.QRCode(box_size=8, border=3)
    qr.add_data(public_url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="#30203d", back_color="#fffaff")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    import base64
    qr_data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return render_template("index.html", qr_data=qr_data, public_url=public_url)


@app.post("/respond")
def respond():
    payload = request.get_json(silent=True) or {}
    answer = payload.get("answer", "")
    allowed = {"Да! 💗", "Конечно да! 💖"}
    if answer not in allowed:
        return jsonify({"ok": False, "error": "Неизвестный вариант ответа."}), 400

    if not BOT_TOKEN or not CHAT_ID:
        app.logger.error("Telegram credentials are not configured.")
        return jsonify({
            "ok": False,
            "error": "Уведомления пока не настроены. Добавьте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в переменные окружения."
        }), 503

    text = (
        "💌 Новое сообщение о свидании!\n\n"
        f"Ответ: {answer}\n"
        "Кажется, это будет мило 🥹💕"
    )
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": text},
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
        if not result.get("ok"):
            app.logger.error("Telegram API returned an unsuccessful response.")
            return jsonify({"ok": False, "error": "Telegram не принял сообщение. Проверьте настройки бота."}), 502
    except requests.RequestException:
        app.logger.exception("Could not send Telegram notification.")
        return jsonify({"ok": False, "error": "Не удалось отправить уведомление в Telegram. Попробуйте позже."}), 502

    return jsonify({"ok": True})


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # For local testing only. Render supplies its own PORT in production.
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
