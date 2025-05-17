import os
from pyexpat.errors import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
import json
import urllib.request
from django.urls import reverse
from dotenv import load_dotenv
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from .models import FavoriteCity

def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, "weather/signup.html", {'form': form})

def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('index')
    return render(request, 'weather/login.html')

def user_logout(request):
    logout(request)
    return redirect('index')

def index(request):
    load_dotenv()
    data = {}
    city_is_favorite = False
    city = request.POST.get('city', '').strip() if request.method == 'POST' else request.GET.get('city', '').strip()
    
    if city:
        apikey = os.getenv('API_KEY')
        if not apikey:
            data['error'] = "API configuration error"
        else:
            try:
                with urllib.request.urlopen(
                    f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid={apikey}&units=metric'
                ) as source:
                    list_of_data = json.loads(source.read())
                    
                    # Check if city exists in response
                    if 'cod' in list_of_data and list_of_data['cod'] != 200:
                        data['error'] = list_of_data.get('message', 'City not found')
                    else:
                        data = {
                            'city': city,
                            'country_code': list_of_data['sys']['country'],
                            'temp': f"{round(list_of_data['main']['temp'])}°C",
                            'feels_like': f"{round(list_of_data['main']['feels_like'])}°C",
                            'pressure': list_of_data['main']['pressure'],
                            'humidity': list_of_data['main']['humidity'],
                            'description': list_of_data['weather'][0]['description'].capitalize(),
                            'wind_speed': f"{round(list_of_data['wind']['speed'] * 3.6)} km/h",  # Convert m/s to km/h
                        }
                        
                        if request.user.is_authenticated:
                            city_is_favorite = FavoriteCity.objects.filter(
                                user=request.user,
                                city=city
                            ).exists()
                            
            except urllib.error.URLError as e:
                data['error'] = f"Network error: {str(e)}"
            except json.JSONDecodeError:
                data['error'] = "Invalid API response"
            except Exception as e:
                data['error'] = f"Unexpected error: {str(e)}"

    return render(request, 'weather/index.html', {
        'data': data,
        'city_is_favorite': city_is_favorite,
        'current_city': city,
    })

@login_required
def toggle_favorite(request):
    if request.method == 'POST':
        city = request.POST.get('city')
        country_code = request.POST.get('country_code', '')
        
        # Get the referring URL or default to index
        next_url = request.POST.get('next', reverse('index'))
        
        if city:
            try:
                fav, created = FavoriteCity.objects.get_or_create(
                    user=request.user,
                    city=city,
                    defaults={'country_code': country_code}
                )
                
                if not created:
                    fav.delete()
            except Exception as e:
                messages.error(request, f"Error updating favorites: {str(e)}")
        
        return redirect(next_url)
    return redirect('index')

@login_required
def favorites_view(request):
    favorites = FavoriteCity.objects.filter(user=request.user)
    return render(request, 'weather/favorites.html', {'favorites': favorites})

