
import requests
from datetime import datetime
from django.shortcuts import render
from django.conf import settings
from datetime import datetime

from django.shortcuts import render, redirect
from .models import Producto

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

def subir_producto(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        desc = request.POST.get('descripcion')
        img = request.FILES.get('imagen')
        
        if img:
            nuevo_producto = Producto(nombre=nombre, descripcion=desc, imagen=img)
            nuevo_producto.save() # .save() asegura la activación del storage de Cloudinary
            return redirect('subir_producto')
    
    productos = Producto.objects.all()
    return render(request, 'comunidad/upload.html', {'productos': productos})

def galeria_imagenes(request):
    # Traemos todos los productos ordenados por el más reciente
    productos = Producto.objects.all().order_by('-id')
    return render(request, 'comunidad/galeria.html', {'productos': productos})