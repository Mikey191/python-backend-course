import json

# Запрашиваем у пользователя имя и email
name = input("Введите имя пользователя: ")
email = input("Введите email пользователя: ")

# Загружаем текущие данные из users.json
with open("users.json", "r", encoding="utf-8") as file:
    users = json.load(file)

# Добавляем нового пользователя
new_user = {"name": name, "email": email}
users.append(new_user)

# Сохраняем обновлённый список обратно в файл
with open("users.json", "w", encoding="utf-8") as file:
    json.dump(users, file, ensure_ascii=False, indent=2)

print("Пользователь успешно добавлен!")