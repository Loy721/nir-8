from django.http import HttpResponse
import tensorflow as tf
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import json
import pandas as pd

history_prediction = []
model = tf.keras.models.load_model("C:\\Users\\dynka\\Downloads\\model.h5")
history_temp_for_n_steps = pd.read_excel('C:\\Users\\dynka\\django\\nir\\nir\\main\\SE_final.xls', skiprows=6)
history_temp_for_n_steps = history_temp_for_n_steps[4:2924]
history_temp_for_n_steps = history_temp_for_n_steps['T'].values[::-1]

def get_actual_temps():
    access_key = 'some-key' # TODO: ключ действует 7 дней

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

def __normalize(data):
    return ((data + 30.6) / (39.7 + 30.6)) * 2 - 1


def denormalize(normalized_data):
    return ((normalized_data + 1) / 2) * (39.7 + 30.6) - 30.6
def predict():
    tmp = __normalize(history_temp_for_n_steps.reshape(1, 1, 1, 2920, 1))
    history_prediction.append(denormalize(model.predict(tmp)))
    print(history_prediction)

def index(request):
    data = []
    current_hour = 0
    for i in range(8):
        temperature = str(round(history_prediction[0][0][i])) # берем последний предикт
        hour = str((current_hour + 1 + i * 3) % 24).zfill(2) # +1 так как по дефолту московское время
        data.append({"time": hour + ':00', "temperature": temperature + '°C'})
    json_data = json.dumps(data)
    return HttpResponse(json_data)


sched = BackgroundScheduler(daemon=True)
sched.add_job(predict, 'interval', hours=3, start_date='2024-05-22 00:00:00')  # TODO: hours=3
sched.start()
predict() # вызываем для начальной инициализации
