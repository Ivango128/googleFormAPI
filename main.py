import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Путь к JSON-файлу с ключами вашей учетной записи
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ['https://www.googleapis.com/auth/forms.body', 'https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

def create_google_form(service, title):
    """
    Создает Google Форму с указанным заголовком и возвращает ее ID.
    """
    form_body = {
        "info": {
            "title": title
        }
    }

    # Создаем пустую форму
    form = service.forms().create(body=form_body).execute()
    form_id = form.get('formId')  # Получаем ID формы

    # Вопросы, которые нужно добавить
    questions = [
        "Формулировка цели проекта",
        "Актуальность проекта",
        "Артистичность выступающего",
        "Качество графического материала",
        "Соответствие функциональным требованиям",
        "Перспективы развития",
        "Реализация проекта",
        "Ответы на вопросы слушателей",
    ]

    # Формируем тело для batchUpdate
    requests = []

    # Добавляем вопросы
    for question in questions:
        requests.append({
            "createItem": {
                "item": {
                    "title": question,
                    "questionItem": {
                        "question": {
                            "required": True,
                            "choiceQuestion": {
                                "type": "RADIO",
                                "options": [{"value": str(i)} for i in range(1, 6)],
                                "shuffle": False
                            }
                        }
                    }
                },
                "location": {
                    "index": 0
                }
            }
        })

    # Отправляем batchUpdate запрос
    service.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
    return form  # Возвращаем ID формы

def update_drive_file_name(form_id, new_name):
    # Обновляем имя файла на Google Drive
    file_metadata = {'name': new_name}
    drive_service.files().update(fileId=form_id, body=file_metadata).execute()


def move_form_to_folder(form_id, folder_id, form_title):
    # Получаем ID файла (форма) из Google Drive
    file = drive_service.files().get(fileId=form_id, fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))

    # Перемещаем форму в нужную папку
    drive_service.files().update(
        fileId=form_id,
        addParents=folder_id,
        removeParents=previous_parents
    ).execute()

    update_drive_file_name(form_id, form_title)

def main():
    # Чтение ФИО из файла
    input_file = "participants.txt"
    if not os.path.exists(input_file):
        print("Файл с участниками не найден!")
        return

    with open(input_file, "r", encoding="utf-8") as file:
        participants = [line.strip() for line in file.readlines() if line.strip()]

    if not participants:
        print("Файл пуст или содержит только пробелы.")
        return

    # Настройка авторизации
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('forms', 'v1', credentials=credentials)

    # Список для хранения данных в формате ФИО, formId
    forms_info = []
    folder_id = "1A3N-FNQR8JcrTlSo7yhKHyCmuFO8R9M8"

    # Создаем формы для каждого участника
    for participant in participants:
        form_title = f"{participant} оценка участника"
        try:
            form = create_google_form(service, form_title)
            form_id = form.get('formId')
            form_link = form.get('responderUri')
            forms_info.append(f"{participant},{form_id}")  # Сохраняем ФИО и ID формы
            move_form_to_folder(form_id, folder_id, form_title)
            print(f"Создана форма для {participant}: link={form_link}")
        except Exception as e:
            print(f"Ошибка при создании формы для {participant}: {e}")

    # Обновляем файл с ФИО в формате ФИО,formId
    output_file = "forms_info.txt"  # Перезаписываем тот же файл
    try:
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(forms_info))
        print(f"Файл '{output_file}' обновлен в формате ФИО,formId.")
    except Exception as e:
        print(f"Ошибка при обновлении файла {output_file}: {e}")


if __name__ == "__main__":
    main()
