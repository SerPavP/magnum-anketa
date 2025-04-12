import json
from tinydb import TinyDB
from datetime import datetime
import os

STATUS_FILE = "status.json"

def run_postsubmit():
    print("[POSTSUBMIT] Загружаем анкету пользователя...")
    with open("user_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    data['timestamp'] = datetime.now().isoformat()
    db = TinyDB("responses.json")
    db.insert(data)

    print(f"[POSTSUBMIT] ✅ Анкета сохранена: {data['fio']} ({data['phone']})")

    # Устанавливаем флаг нового обновления
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump({"new_update": True}, f)
    print("[POSTSUBMIT] 🚨 Установлен флаг нового обновления для администратора.")

def clear_update_flag():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump({"new_update": False}, f)
        print("[POSTSUBMIT] ✅ Флаг обновления сброшен.")
