# Выкачиваем из dockerhub образ с python версии 3.9
FROM python:3.9
# Устанавливаем рабочую директорию для проекта в контейнере
WORKDIR /planner
# Скачиваем/обновляем необходимые библиотеки для проекта 
COPY ./requirements.txt /planner
RUN pip3 install --upgrade pip -r requirements.txt
# копируем содержимое папки, где находится Dockerfile,
# в рабочую директорию контейнера
COPY . /planner
# Устанавливаем порт, который будет использоваться для сервера
EXPOSE 8080
ENTRYPOINT ["python"]
CMD ["main.py"]

