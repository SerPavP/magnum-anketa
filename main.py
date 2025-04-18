from flask import Flask, render_template, request, redirect, url_for, send_file, Response
import asyncio
import json
import re
from parser import run_parser, FormValidationError
from tinydb import TinyDB
from postsubmit import clear_update_flag, clear_database
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from base64 import b64decode

app = Flask(__name__)
executor = ThreadPoolExecutor()

logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

BRANCH_ADDRESSES = {
    "City Plus": "Алматы, Толе би 285",
    "Market Hall": "Алматы, Байтурсынова 22",
    "Алаш": "Астана, Шоссе Алаш 23/1",
    "Кен Март": "Астана, Трасса Астана-Караганда 45",
    "Бекжан": "Шымкент, Жиделбайсына 92",
    "Кульджинский тракт": "Алматы, Кульджинский тракт 22/6"
}

ADMIN_PASSWORD = "magnumGOOD"

def check_auth(header):
    if not header or not header.startswith("Basic "):
        return False
    try:
        auth_decoded = b64decode(header.split(" ")[1]).decode("utf-8")
        username, password = auth_decoded.split(":", 1)
        return password == ADMIN_PASSWORD
    except Exception:
        return False

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not check_auth(auth):
            return Response(
                "Необходима авторизация", 401,
                {"WWW-Authenticate": "Basic realm='Login Required'"}
            )
        return f(*args, **kwargs)
    return decorated

@app.route("/", methods=["GET"])
def index():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    try:
        fio = request.form['fio']
        phone = request.form['phone']
        iin = request.form['iin']
        branch = request.form['branch']

        phone_digits = re.sub(r'\D', '', phone)
        if phone_digits.startswith('7'):
            phone_digits = phone_digits[1:]
        if len(phone_digits) != 10:
            return render_template("form.html", error="Номер телефона должен состоять из 10 цифр.")

        user_data = {
            'fio': fio,
            'phone': phone_digits,
            'iin': iin,
            'branch': branch
        }

        with open("user_data.json", "w", encoding="utf-8") as f:
            json.dump(user_data, f, ensure_ascii=False, indent=2)

        try:
            asyncio.run(run_parser())
            return render_template("thank_you.html", fio=fio, branch_address=BRANCH_ADDRESSES.get(branch, "уточните адрес у администратора"))
        except FormValidationError as e:
            logging.error(f"Ошибка при валидации формы: {e}")
            return render_template("form.html", error=str(e))
        except Exception as e:
            logging.exception("Непредвиденная ошибка парсера")
            return render_template("form.html", error="Что-то пошло не так, попробуйте позже.")

    except Exception as global_error:
        logging.exception("Критическая ошибка обработки submit")
        return render_template("form.html", error="Что-то не получилось, попробуйте через пару минут")

@app.route("/favicon.ico")
def favicon():
    try:
        with open("status.json", "r", encoding="utf-8") as f:
            status = json.load(f)
        icon = "favicon_red.ico" if status.get("new_update") else "favicon.ico"
        return send_file(icon)
    except Exception:
        return "", 204

@app.route("/admin")
@requires_auth
def admin():
    clear_update_flag()
    db = TinyDB("responses.json")
    responses = db.all()
    return render_template("admin.html", responses=responses)

@app.route("/admin/clear")
@requires_auth
def admin_clear():
    clear_database()
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
