#!/usr/bin/env python3
import urllib.request
import json

def get_temperature():
    city = "Buenos Aires"
    try:
        # Using wttr.in API to get weather data
        url = "https://wttr.in/Buenos_Aires?format=j1"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())
            temp_c = data['current_condition'][0]['temp_C']
            print(f"City: {city}")
            print(f"Temperature: {temp_c}C")
    except Exception as e:
        print(f"Error fetching temperature: {e}")

if __name__ == "__main__":
    get_temperature()
