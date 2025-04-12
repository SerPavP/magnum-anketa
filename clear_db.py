from tinydb import TinyDB

db = TinyDB("responses.json")
db.truncate()
print("✅ База данных очищена.")
