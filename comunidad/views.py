from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return HttpResponse("Hello World")
import requests
from django.shortcuts import render
from django.conf import settings
from datetime import datetime # Para convertir la hora

def ver_clima(request):
    api_key = settings.OPENWEATHER_API_KEY
    lat, lon = -26.3592, -52.8511
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
    
    try:
        response = requests.get(url)
        datos = response.json()
        
        if response.status_code == 200:
            # Conversión de horas UNIX a formato legible (HH:MM)
            sunrise = datetime.fromtimestamp(datos['sys']['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(datos['sys']['sunset']).strftime('%H:%M')
            
            contexto = {
                'ok': True,
                'ciudad': "São Lourenço do Oeste",
                'temperatura': datos['main'].get('temp'),
                'feels_like': datos['main'].get('feels_like'), # SENSACIÓN TÉRMICA
                'min': datos['main'].get('temp_min'),
                'max': datos['main'].get('temp_max'),
                'presion': datos['main'].get('pressure'),     # PRESIÓN hPa
                'humedad': datos['main'].get('humidity'),
                'visibilidad': datos.get('visibility') / 1000, # Convertir a KM
                'viento': datos['wind'].get('speed'),
                'nubes': datos['clouds'].get('all'),          # % de NUBOSIDAD
                'amanecer': sunrise,
                'atardecer': sunset,
                'descripcion': datos['weather'][0].get('description'),
                'icono': datos['weather'][0].get('icon'),
                'latitud': lat,
                'longitud': lon,
            }
        else:
            contexto = {'ok': False, 'error_msg': datos.get('message')}
    except Exception:
        contexto = {'ok': False, 'error_msg': "Error de conexión"}

    return render(request, 'comunidad/clima.html', contexto)

def air_quality_view(request):
    api_key = settings.OPENWEATHER_API_KEY
    lat, lon = -26.3592, -52.8511
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

    # Diccionario para interpretar el índice AQI
    AQI_MAP = {
        1: {'texto': 'Excelente', 'color': '#2ecc71'},
        2: {'texto': 'Bueno', 'color': '#f1c40f'},
        3: {'texto': 'Moderado', 'color': '#e67e22'},
        4: {'texto': 'Pobre', 'color': '#e74c3c'},
        5: {'texto': 'Muy Pobre', 'color': '#8e44ad'},
    }

    try:
        response = requests.get(url).json()
        raw_aqi = response['list'][0]['main']['aqi']
        componentes = response['list'][0]['components']
        
        context = {
            'aqi_num': raw_aqi,
            'aqi_info': AQI_MAP.get(raw_aqi),
            'pm25': componentes['pm2_5'],
            'pm10': componentes['pm10'],
            'co': componentes['co'],
            'o3': componentes['o3'],
        }
    except Exception:
        context = {'error': "Error al conectar con el servicio de monitoreo."}

    return render(request, 'comunidad/air_quality.html', context)

def mapa_comunidad(request):
    return render(request, 'comunidad/mapa_libre.html', {
        'lat': -26.3592,
        'lon': -52.8511,
    })

import requests
from datetime import datetime
from django.shortcuts import render
from django.conf import settings
from datetime import datetime

def ver_clima_comunitario(request):
    api_key = settings.OPENWEATHER_API_KEY
    lat, lon = -26.3592, -52.8511
    
    url_clima = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric&lang=es"
    url_aire = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"

    try:
        res_clima = requests.get(url_clima).json()
        res_aire = requests.get(url_aire).json()

        if res_clima.get('cod') == 200:
            clima_data = res_clima['main']
            aire_comp = res_aire['list'][0]['components']
            
            # --- Extracción de Datos Base ---
            temp = clima_data.get('temp', 0)
            st = clima_data.get('feels_like', 0)
            humedad = clima_data.get('humidity', 0)
            presion = clima_data.get('pressure', 0)
            viento_ms = res_clima.get('wind', {}).get('speed', 0)
            viento_kmh = viento_ms * 3.6  # Conversión a km/h para SLO
            
            pm25 = aire_comp.get('pm2_5', 0)
            pm10 = aire_comp.get('pm10', 0)
            
            # --- Inicialización del Semáforo de Salud ---
            consejos = []
            riesgo = "Bajo"
            color_alerta = "success"

            # 1. LÓGICA DE TEMPERATURA Y VESTIMENTA (Ajustada a frío de SC)
            if st < 5:
                riesgo = "Alto"; color_alerta = "danger"
                consejos.append("Frío Extremo: Riesgo de hipotermia. Limita tiempo fuera.")
            elif 5 <= st < 13:
                riesgo = "Moderado"; color_alerta = "warning"
                consejos.append("Frío Intenso: Usa ropa térmica y protege nariz/boca.")
            elif 13 <= st < 18:
                consejos.append("Clima Fresco: Una chaqueta abrigada es suficiente.")
            elif st >= 30:
                riesgo = "Moderado"; color_alerta = "warning"
                consejos.append("Calor: Riesgo de deshidratación. Bebe agua constante.")

            # 2. LÓGICA DE VIENTO Y SENSACIÓN TÉRMICA
            if viento_kmh > 30:
                riesgo = "Moderado"
                consejos.append(f"Viento Fuerte ({round(viento_kmh)} km/h): Asegura objetos sueltos.")
            elif viento_kmh > 15 and st < 15:
                consejos.append("Efecto Chill: El viento aumenta el frío. Abrígate más.")

            # 3. LÓGICA DE HUMEDAD (Salud Respiratoria)
            if humedad < 30:
                consejos.append("Aire Seco: Hidrata tu nariz y bebe mucha agua.")
            elif humedad > 85:
                consejos.append("Humedad Alta: Ventila ambientes para evitar moho.")

            # 4. PRESIÓN (Alerta de Tormenta)
            if presion < 1005:
                consejos.append("Presión Baja: El tiempo puede volverse inestable pronto.")

            # 5. CALIDAD DEL AIRE (Expert Mode - Estándar OMS)
            if pm25 > 15:
                aire_estado, aire_color = "Malo", "danger"
                riesgo, color_alerta = "Alto", "danger"
                consejos.append("Calidad Aire: Nociva. Grupos sensibles deben quedarse en casa.")
            elif pm25 > 5:
                aire_estado, aire_color = "Moderado", "warning"
                consejos.append("Calidad Aire: Regular. Evita ejercicio intenso al aire libre.")
            else:
                aire_estado, aire_color = "Excelente", "success"

            contexto = {
                'ok': True,
                'ciudad': "São Lourenço do Oeste",
                'temperatura': temp,
                'feels_like': st,
                'descripcion': res_clima['weather'][0].get('description').capitalize(),
                'icono': res_clima['weather'][0].get('icon'),
                'humedad': humedad,
                'latitud': lat,
                'longitud': lon,
                'viento': round(viento_kmh, 1), # Se envía ya en km/h
                'presion': presion,
                'aire': {
                    'pm25': pm25,
                    'pm10': pm10,
                    'estado': aire_estado,
                    'color_clase': aire_color,
                },
                'salud': {
                    'nivel_riesgo': riesgo,
                    'color': color_alerta, 
                    'recomendaciones': consejos 
                },
                'fecha': datetime.now().strftime('%H:%M')
            }
        else:
            contexto = {'ok': False, 'error_msg': f"Error API: {res_clima.get('message')}"}

    except Exception as e:
        contexto = {'ok': False, 'error_msg': f"Error técnico: {str(e)}"}

    return render(request, 'comunidad/clima_comunitario.html', contexto)