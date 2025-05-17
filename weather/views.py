import os
from django.shortcuts import render
import json
import urllib.request
from dotenv import load_dotenv

# Create your views here.
def index(request):
    data = {}
    load_dotenv()
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        if city:
            # apikey = 'd736ba51d19cb0bf57acb1810330b424'
            apikey = os.getenv('API_KEY')
            try:
                source = urllib.request.urlopen(
                    f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={apikey}&units=metric').read()
                list_of_data = json.loads(source)
                data = {
                    'city': city,
                    'country_code': list_of_data['sys']['country'],
                    'temp': f"{round(list_of_data['main']['temp'])}°C",
                    'pressure': list_of_data['main']['pressure'],
                    'humidity': list_of_data['main']['humidity'],
                    'description': list_of_data['weather'][0]['description'],
                    'icon': list_of_data['weather'][0]['icon'],
                    'wind_speed': list_of_data['wind']['speed'],
                }
            except Exception as e:
                data['error'] = f"Error fetching weather data: {str(e)}"
    return render(request, 'weather/index.html', {'data': data})  