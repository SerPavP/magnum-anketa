from playwright.async_api import async_playwright
import json
import asyncio
import re
from postsubmit import run_postsubmit

class FormValidationError(Exception):
    pass

async def run_parser():
    print("[PARSER] Чтение данных из user_data.json...")
    with open("user_data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    print("[PARSER] Данные загружены:")
    print(data)

    phone_digits = data['phone']
    formatted_phone = f"+7({phone_digits[:3]}){phone_digits[3:6]}-{phone_digits[6:8]}-{phone_digits[8:]}"

    async with async_playwright() as p:
        print("[PARSER] Запуск браузера...")
        browser = await p.chromium.launch(headless=True)  # теперь headless для сервера
        page = await browser.new_page()

        print("[PARSER] Переход на страницу анкеты...")
        await page.goto("https://mecom-int.kz/page64501793.html")
        await asyncio.sleep(2)

        print("[PARSER] Заполнение ФИО...")
        await page.fill("input[name='ФИО Кандидата']", data['fio'])
        print("[PARSER] Заполнение ИИН...")
        await page.fill("input[name='ИИН Кандидата']", data['iin'])

        print("[PARSER] Очистка и вставка номера телефона...")
        await page.fill("input[name='Номер Кандидата']", "")
        await page.type("input[name='Номер Кандидата']", formatted_phone, delay=100)

        print("[PARSER] Выбор филиала...")
        await page.select_option("select[name='Филиал Кандидата']", label=data['branch'])

        print("[PARSER] Выбор сектора...")
        await page.wait_for_selector("select[name='Сектор Кандидата']")
        await page.click("select[name='Сектор Кандидата']")
        await page.select_option("select[name='Сектор Кандидата']", label="Сектор Доставки заказов")

        print("[PARSER] Установка должности 'Курьер'...")
        await page.click("label:has-text('Курьер')")

        print("[PARSER] Кнопка 'Вперед'...")
        await page.wait_for_selector("button.t-form__screen-btn-next")
        await page.click("button.t-form__screen-btn-next")

        print("[PARSER] Проверка перехода к анкете сотрудника...")
        await asyncio.sleep(0.5)
        heading = await page.query_selector("p:has-text('Анкета Сотрудника')")
        if not heading:
            error_warning = await page.query_selector("sub:has-text('Пожалуйста, заполните свои данные внимательно')")
            if error_warning:
                await browser.close()
                raise FormValidationError("Данные были некорректны. Проверьте правильность заполнения формы.")

            fio_error = await page.query_selector(".js-errorbox-item.js-rule-error-name")
            if fio_error and await fio_error.is_visible():
                await browser.close()
                raise FormValidationError("Поле ФИО заполнено неправильно. Пожалуйста, введите корректное имя.")

        print("[PARSER] Заполнение анкеты сотрудника...")
        await page.fill("input[name='ФИО Сотрудника']", "Ракин Алексей")
        await page.fill("input[name='ИИН Сотрудника']", "910205351188")
        await page.fill("input[name='Номер Сотрудника']", "")
        await page.type("input[name='Номер Сотрудника']", "87002980069", delay=150)

        await page.select_option("select[name='Филиал Сотрудника']", label="Кен Март")
        await page.select_option("select[name='Сектор Сотрудника']", label="Сектор Доставки заказов")

        print("[PARSER] Установка должности 'Курьер' (сотрудник)...")
        await page.wait_for_selector("label.t-radio__item:has(input[name='Должность Сотрудника'][value='Курьер'])", state="visible", timeout=10000)
        await page.click("label.t-radio__item:has(input[name='Должность Сотрудника'][value='Курьер'])")

        print("[PARSER] Подтверждение согласия...")
        await page.wait_for_selector("label.t-checkbox__control:has(input[name='Согласие'])", state="visible", timeout=10000)
        await page.click("label.t-checkbox__control:has(input[name='Согласие'])")

        print("[PARSER] Отправка формы... нажимаем кнопку 'Отправить / Жіберу'")
        await page.wait_for_selector("button.t-submit", timeout=10000)
        await page.click("button.t-submit")

        print("[PARSER] ✅ Все поля успешно заполнены и форма отправлена.")
        print("[PARSER] ✅ Запуск postsubmit...")
        run_postsubmit()
        await browser.close()
