import json
import requests
from datetime import datetime, timedelta
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def index(request):
    return render(request, 'weather_app/index.html')

@csrf_exempt
def get_weather(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            api_key = settings.OPENWEATHER_API_KEY
            print("API KEY:", api_key)

            # Get location data
            location_query = data.get('location')
            if location_query:
                # Search by location name or zip code
                url = f'https://api.openweathermap.org/data/2.5/weather?q={location_query}&appid={api_key}&units=metric'
            else:
                # Use geolocation
                lat = data.get('latitude')
                lon = data.get('longitude')
                
                if not lat or not lon:
                    return JsonResponse({'error': 'Location data not provided'}, status=400)
                
                url = f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric'
            
            # Get current weather
            response = requests.get(url)
            current_weather = response.json()
            print("Current Weather API response:", current_weather)

            if response.status_code != 200:
                return JsonResponse({'error': current_weather.get('message', 'Failed to fetch weather data')}, status=500)

            # Get coordinates from current weather response
            lat = current_weather['coord']['lat']
            lon = current_weather['coord']['lon']

            # Get forecast data
            forecast_url = f'https://api.openweathermap.org/data/2.5/forecast?q={current_weather["name"]}&appid={api_key}&units=metric'
            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()

            if forecast_response.status_code != 200:
                return JsonResponse({'error': forecast_data.get('message', 'Failed to fetch forecast data')}, status=500)

            # Process forecast data
            daily_forecasts = {}
            for item in forecast_data['list']:
                date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
                if date not in daily_forecasts:
                    daily_forecasts[date] = {
                        'dt': item['dt'],
                        'temp': item['main']['temp'],
                        'description': item['weather'][0]['description'],
                        'humidity': item['main']['humidity'],
                        'wind_speed': item['wind']['speed'],
                        'icon': item['weather'][0]['icon']
                    }

            # Get hourly forecast data for the next 24 hours
            hourly_forecast = []
            for item in forecast_data['list'][:8]:  # Get next 24 hours (8 3-hour intervals)
                hourly_forecast.append({
                    'dt': item['dt'],
                    'temp': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'humidity': item['main']['humidity'],
                    'wind_speed': item['wind']['speed'],
                    'icon': item['weather'][0]['icon']
                })

            response_data = {
                'current': {
                    'temperature': current_weather['main']['temp'],
                    'description': current_weather['weather'][0]['description'],
                    'humidity': current_weather['main']['humidity'],
                    'wind_speed': current_weather['wind']['speed'],
                    'city': current_weather['name'],
                    'country': current_weather['sys']['country'],
                    'icon': current_weather['weather'][0]['icon']
                },
                'forecast': list(daily_forecasts.values()),
                'hourly': hourly_forecast
            }

            return JsonResponse(response_data)

        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400) 