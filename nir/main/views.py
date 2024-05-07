import numpy as np
from django.http import HttpResponse
import tensorflow as tf
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import json
from datetime import datetime

# Create your views here.

history_prediction = []
model = tf.keras.models.load_model("C:\\Users\\dynka\\IdeaProjects\\Python\\NIR2\\mlp_model")
history_temp_for_n_steps = np.array(
    [12, 10, 10, 12, 10, 10, 12, 10, 9, 8, 7, 11, 15, 18, 17])  # TODO: перед деплоем вставить акутальные данные


def get_actual_temps():
    access_key = '5ae88ab3-9162-4b83-a324-5a43890af3dc' # TODO: ключ действует 7 дней

    headers = {
        "X-Yandex-API-Key": access_key
    }

    query = """{
      weatherByPoint(request: { lat: 53.195877, lon: 50.100201 }) {
        now {
          temperature
        }
      }
    }"""
    response = requests.post('https://api.weather.yandex.ru/graphql/query', headers=headers, json={'query': query})
    now_temperature = response.json()["data"]["weatherByPoint"]["now"]["temperature"]
    return now_temperature


def predict():
    now_temperature = get_actual_temps()
    history_temp_for_n_steps[:15 - 1] = history_temp_for_n_steps[1:15]
    history_temp_for_n_steps[15 - 1] = now_temperature

    ls = []
    dat = history_temp_for_n_steps.copy()
    for i in range(0, 7):
        ls.append(model.predict(dat.reshape(1, 15), verbose=0)[0])
        dat[:15 - 1] = dat[1:15]
        dat[15 - 1] = ls[i]
    history_prediction.append(ls)


def index(request):
    data = []
    current_hour = datetime.now().hour
    for i in range(7):
        temperature = str(round(history_prediction[len(history_prediction) - 1][i][0])) # берем последний предикт
        hour = str((current_hour + 1 + i * 3) % 24).zfill(2) # +1 так как по дефолту московское время
        data.append({"time": hour + ':00', "temperature": temperature + '°C'})
    json_data = json.dumps(data)
    return HttpResponse(json_data)


sched = BackgroundScheduler(daemon=True)
sched.add_job(predict, 'interval', hours=3, start_date='2024-04-16 23:00:00')  # TODO: hours=3
sched.start()
predict() # вызываем для начальной инициализации
