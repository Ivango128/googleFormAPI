import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import numpy as np  # Для вычисления среднего значения
from numpy.ma.core import count

# Путь к JSON-файлу с ключами вашей учетной записи
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/forms.responses.readonly"]


def fetch_responses(service, form_id):
    """
    Извлекает ответы из Google Формы.
    """
    responses = service.forms().responses().list(formId=form_id).execute()
    return responses.get('responses', [])


def calculate_average_scores(responses, count_forms):
    """
    Вычисляет средний балл по каждому вопросу и общий средний балл.
    """
    if not responses:
        return None  # Если ответов нет

    scores = []  # Список всех ответов
    if len(responses) > count_forms:
        return "1"
    elif len(responses) < count_forms:
        return "2"
    for response in responses:
        # Ответы на вопросы
        answers = response.get('answers', {})
        question_scores = []
        for question_id, answer in answers.items():
            try:
                # Извлекаем числовое значение ответа
                score = int(answer['textAnswers']['answers'][0]['value'])
                question_scores.append(score)
            except (KeyError, ValueError, IndexError):
                pass  # Пропускаем некорректные данные
        if question_scores:
            scores.append(question_scores)

    if not scores:
        return None

    # Преобразуем список в numpy массив для удобства
    scores_array = np.array(scores)
    average_scores_per_question = np.mean(scores_array, axis=0)  # Среднее по каждому вопросу
    overall_average_score = np.mean(scores_array)  # Общий средний балл
    return average_scores_per_question, overall_average_score



def main():
    # Чтение ФИО и ID форм из файла
    forms_file = "forms_info.txt"
    if not os.path.exists(forms_file):
        print("Файл с информацией о формах не найден!")
        return

    with open(forms_file, "r", encoding="utf-8") as file:
        forms = [line.strip().split(",") for line in file.readlines() if line.strip()]
        count_forms = len(forms)


    if not forms:
        print("Файл пуст или содержит некорректные данные.")
        return

    # Настройка авторизации
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('forms', 'v1', credentials=credentials)

    # Обработка каждой формы
    for form in forms:
        try:
            fio, form_id = form  # Ожидается формат: "ФИО,formId"
            responses = fetch_responses(service, form_id)
            averages = calculate_average_scores(responses, count_forms)
            if averages == "1":
                print(f"{fio}: Фальсификация данных. Голосов больше чем участников голосования.")
            elif averages == "2":
                print(f"{fio}: Фальсификация данных. Голосов меньше чем участников голосования.")
            elif averages:
                _, overall_average_score = averages
                print(f"{fio} {overall_average_score:.2f}")
            else:
                print(f"{fio}: Нет данных для подсчета среднего балла.")
        except Exception as e:
            print(f"Ошибка при обработке формы для {form[0]}: {e}")


if __name__ == "__main__":
    main()
