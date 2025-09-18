import requests

city = input("Введите название города: ")
url = f"https://wttr.in/{city}"

try:
    response = requests.get(url)
    print(response.text)
except Exception:
    print("Упс! Что-то пошло не так. Попробуйте позже.")
