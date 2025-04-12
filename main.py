from flask import Flask, render_template_string, request, redirect, url_for, send_file
import asyncio
import json
import re
import os
from parser import run_parser, FormValidationError
from tinydb import TinyDB
from postsubmit import clear_update_flag

app = Flask(__name__)

BRANCH_ADDRESSES = {
    "City Plus": "Алматы, Толе би 285",
    "Market Hall": "Алматы, Байтурсынова 22",
    "Алаш": "Астана, Шоссе Алаш 23/1",
    "Кен Март": "Астана, Трасса Астана-Караганда 45",
    "Бекжан": "Шымкент, Жиделбайсына 92",
    "Кульджинский тракт": "Алматы, Кульджинский тракт 22/6"
}

FORM_HTML_TEMPLATE = """
<!doctype html>
<html lang=\"ru\">
  <head>
    <meta charset=\"utf-8\">
    <title>Анкета</title>
    <script src=\"https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js\"></script>
    <script src=\"https://cdnjs.cloudflare.com/ajax/libs/jquery.mask/1.14.16/jquery.mask.min.js\"></script>
    <style>
      body {
        background-color: #e5007d;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
      }
      .form-container {
        background: white;
        color: #333;
        padding: 30px 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        width: 100%;
        max-width: 420px;
        box-sizing: border-box;
      }
      .form-container h2 {
        text-align: center;
        margin-bottom: 25px;
        color: #e5007d;
      }
      .error-message {
        color: red;
        font-size: 14px;
        margin-bottom: 10px;
        text-align: center;
      }
      label {
        font-weight: bold;
        display: block;
        margin-top: 15px;
      }
      input, select, button {
        width: 100%;
        padding: 12px;
        margin-top: 8px;
        border-radius: 8px;
        border: 1px solid #ccc;
        box-sizing: border-box;
        font-size: 14px;
      }
      button {
        background-color: #e5007d;
        color: white;
        font-weight: bold;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s;
        margin-top: 20px;
      }
      button:hover {
        background-color: #c1006a;
      }
    </style>
    <script>
      $(document).ready(function(){
        $('input[name=\"phone\"]').mask('+7(000)000-0000');
        $('input[name=\"iin\"]').mask('000000000000');

        $('form').on('submit', function(e) {
          const phone = $('input[name=\"phone\"]').val();
          const iin = $('input[name=\"iin\"]').val();

          if (phone.length < 10) {
            alert("Пожалуйста, введите полный номер телефона.");
            e.preventDefault();
          }
          if (iin.length < 12) {
            alert("Пожалуйста, введите корректный ИИН из 12 цифр.");
            e.preventDefault();
          }
        });
      });
    </script>
  </head>
  <body>
    <div class=\"form-container\">
      <h2>Анкета пользователя</h2>
      {% if error %}<div class=\"error-message\">{{ error }}</div>{% endif %}
      <form method=\"POST\" action=\"/submit\">
        <label>ФИО</label>
        <input type=\"text\" name=\"fio\" required />

        <label>Телефон</label>
        <input type=\"text\" name=\"phone\" required placeholder=\"+7(777)000-0000\" />

        <label>ИИН</label>
        <input type=\"text\" name=\"iin\" required placeholder=\"010205151152\" />

        <label>Филиал</label>
        <select name=\"branch\">
          <option value=\"\">Выберите вариант из списка...</option>
          <option value=\"City Plus\">Алматы \"City Plus\" Толе би 285</option>
          <option value=\"Market Hall\">Алматы \"Market Hall\" Байтурсынова 22</option>
          <option value=\"Алаш\">Астана \"Алаш\" Шоссе Алаш 23/1</option>
          <option value=\"Кен Март\">Астана \"КенМарт\" Трасса Астана-Караганда 45</option>
          <option value=\"Бекжан\">Шымкент \"Бекжан\" Жиделбайсына 92</option>
          <option value=\"Кульджинский тракт\">Алматы \"Кульджинский тракт\" Кульджинский тракт 22/6</option>
        </select>

        <button type=\"submit\">Отправить</button>
      </form>
    </div>
  </body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    print("[INFO] Открыта страница анкеты")
    return render_template_string(FORM_HTML_TEMPLATE)

@app.route("/submit", methods=["POST"])
def submit():
    print("[INFO] Форма отправлена пользователем")
    fio = request.form['fio']
    phone = request.form['phone']
    iin = request.form['iin']
    branch = request.form['branch']

    phone_digits = re.sub(r'\D', '', phone)
    if phone_digits.startswith('7'):
        phone_digits = phone_digits[1:]
    if len(phone_digits) != 10:
        return render_template_string(FORM_HTML_TEMPLATE, error="Номер телефона должен состоять из 10 цифр.")

    print(f"[DATA] ФИО: {fio}")
    print(f"[DATA] Телефон (отформатированный для json): {phone_digits}")
    print(f"[DATA] ИИН: {iin}")
    print(f"[DATA] Филиал: {branch}")

    user_data = {
        'fio': fio,
        'phone': phone_digits,
        'iin': iin,
        'branch': branch
    }

    with open("user_data.json", "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)
        print("[INFO] Данные пользователя сохранены в user_data.json")

    try:
        print("[INFO] Запуск парсера Playwright...")
        asyncio.run(run_parser())
        print("[INFO] Парсер завершил работу")
    except FormValidationError as e:
        print(f"[ERROR] Ошибка при валидации формы: {e}")
        return render_template_string(FORM_HTML_TEMPLATE, error=str(e))

    branch_address = BRANCH_ADDRESSES.get(branch, "уточните адрес у администратора")

    return f"""
    <html><head><meta charset='utf-8'></head>
    <body style='background-color:#e5007d;color:white;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;text-align:center;'>
    <div>
      <h2>Спасибо, {fio}!</h2>
      <p>Ждём вас на собеседование по будням в 10:00</p>
      <p><strong>{branch_address}</strong></p>
    </div>
    </body></html>
    """


@app.route("/favicon.ico")
def favicon():
    with open("status.json", "r", encoding="utf-8") as f:
        status = json.load(f)
    icon = "favicon_red.ico" if status.get("new_update") else "favicon.ico"
    return send_file(icon)

@app.route("/admin")
def admin():
    clear_update_flag()
    db = TinyDB("responses.json")
    responses = db.all()
    return render_template_string("""
    <html>
    <head>
        <meta charset='utf-8'>
        <title>Анкеты</title>
        <link rel='icon' href='/favicon.ico'>
        <script>
            setInterval(() => {
                location.reload();
            }, 10000); // автообновление раз в 10 сек
        </script>
    </head>
    <body style="font-family: sans-serif; padding: 20px;">
        <h1>📥 Новые анкеты</h1>
        {% for r in responses[::-1] %}
            <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ccc; border-radius: 8px;">
                <strong>{{ r.fio }}</strong><br>
                📱 Телефон: {{ r.phone }}<br>
                🆔 ИИН: {{ r.iin }}<br>
                🏢 Филиал: {{ r.branch }}<br>
                🕒 Время: {{ r.timestamp }}
            </div>
        {% endfor %}
    </body>
    </html>
    """, responses=responses)


if __name__ == "__main__":
    print("[INFO] Запуск Flask-сервера...")
    app.run(debug=True)