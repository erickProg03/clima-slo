
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
                consejos.append("Frio Extremo: Risco de hipotermia. Limite o tempo ao ar livre.")
            elif 5 <= st < 13:
                riesgo = "Moderado"; color_alerta = "warning"
                consejos.append("Frio Intenso: Use roupas térmicas e proteja nariz e boca.")
            elif 13 <= st < 18:
                consejos.append("Clima Fresco: Uma jaqueta reforçada é suficiente.")
            elif st >= 30:
                riesgo = "Moderado"; color_alerta = "warning"
                consejos.append("Calor: Risco de desidratação. Beba água constantemente.")

            # 2. LÓGICA DE VENTO E SENSAÇÃO TÉRMICA
            if viento_kmh > 30:
                riesgo = "Moderado"
                consejos.append(f"Vento Forte ({round(viento_kmh)} km/h): Cuidado com objetos soltos.")
            elif viento_kmh > 15 and st < 15:
                consejos.append("Efeito Chill: O vento aumenta a sensação de frio. Agasalhe-se bem.")

            # 3. LÓGICA DE UMIDADE (Saúde Respiratória)
            if humedad < 30:
                consejos.append("Ar Seco: Hidrate o nariz e beba muita água.")
            elif humedad > 85:
                consejos.append("Umidade Alta: Ventile os ambientes para evitar mofo.")

            # 4. PRESSÃO (Alerta de Tempestade)
            if presion < 1005:
                consejos.append("Pressão Baixa: O tempo pode ficar instável em breve.")

            # 5. QUALIDADE DO AR (Expert Mode - Padrão OMS)
            if pm25 > 15:
                aire_estado, aire_color = "Ruim", "danger"
                riesgo, color_alerta = "Alto", "danger"
                consejos.append("Qualidade do Ar: Nociva. Grupos sensíveis devem ficar em casa.")
            elif pm25 > 5:
                aire_estado, aire_color = "Moderada", "warning"
                consejos.append("Qualidade do Ar: Regular. Evite exercícios intensos ao ar livre.")
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
