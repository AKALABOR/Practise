import requests
import time
import random

API_URL = "http://localhost:8000/measurements/"

SENSORS = [
    {"sensor_id": 1, "location": "Kyiv", "unit": "C", "base_temp": 22.0, "variance": 2.0},
    {"sensor_id": 2, "location": "Lviv", "unit": "C", "base_temp": 18.0, "variance": 3.0},
    {"sensor_id": 3, "location": "Odesa", "unit": "C", "base_temp": 25.0, "variance": 1.5},
]

def generate_payload(sensor):
    current_value = round(random.uniform(sensor["base_temp"] - sensor["variance"], 
                                       sensor["base_temp"] + sensor["variance"]), 2)
    
    return {
        "sensor_id": sensor["sensor_id"],
        "value": current_value,
        "unit": sensor["unit"],
        "metadata_info": {"location": sensor["location"]}
    }

def run_emulation(cycles=10, delay_seconds=2):    
    for cycle in range(1, cycles + 1):
        for sensor in SENSORS:
            payload = generate_payload(sensor)
            response = requests.post(API_URL, json=payload)
            if response.status_code == 201:
                data = response.json()
                short_hash = data['data_hash'][:8] + "..."
                print(f"Сенсор {sensor['sensor_id']} ({sensor['location']}) відправив: {payload['value']}°C")

if __name__ == "__main__":
    run_emulation(cycles=5, delay_seconds=1)