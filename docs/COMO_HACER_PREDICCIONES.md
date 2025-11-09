# 📖 Guía: Cómo Hacer Predicciones

Esta guía te muestra **paso a paso** cómo hacer predicciones con el bot.

---

## 🎯 ¿Qué es una Predicción?

Una predicción en el contexto del bot es:

1. **Obtener datos históricos** del jugador/equipo
2. **Calcular probabilidades** de que ocurra un evento
3. **Comparar** con las cuotas de las casas de apuestas
4. **Identificar value bets** (apuestas con Expected Value positivo)
5. **Generar recomendación** con enlace directo para apostar

---

## 🚀 Flujo Completo en 6 Pasos

### **PASO 1: Obtener Estadísticas** 📊

```python
from src.ingest.nba_scraper import NBAStatsScraper

# Inicializar scraper
scraper = NBAStatsScraper()

# Obtener últimos partidos
game_log = scraper.get_player_game_log(
    player_name="LeBron James",
    season="2024-25",
    last_n_games=10
)

# Calcular promedios
avg_points = game_log['PTS'].mean()      # Ej: 25.3
std_points = game_log['PTS'].std()       # Ej: 6.2
```

**Para otros deportes:**
- ACB: `from src.ingest.acb_scraper import ACBScraper`
- La Liga: `from src.ingest.soccer_scraper import SofaScoreSoccerScraper`
- Tenis: `from src.ingest.tennis_scraper import SofaScoreTennisScraper`

---

### **PASO 2: Obtener Cuotas Actuales** 💰

```python
from src.ingest.odds_collector import MultiBookCollector

# Configurar
config = {
    'the_odds_api': {
        'enabled': True,
        'api_key': 'tu_api_key'  # Obtener en https://the-odds-api.com/
    }
}

collector = MultiBookCollector(config)

# Obtener odds de NBA
odds_data = collector.collect_all_odds(
    sports=['nba'],
    markets=['player_points', 'player_rebounds', 'player_assists']
)

# Las odds ya vienen con URLs de bookmakers
for event in odds_data['nba']:
    for bookmaker in event['bookmakers']:
        print(f"{bookmaker['display_name']}: {bookmaker['betting_url']}")
```

**Importante:** Las cuotas ya incluyen las URLs directas a las casas de apuestas.

---

### **PASO 3: Hacer Predicción con el Modelo** 🎯

```python
from src.models.poisson_model import PoissonPropModel

# Inicializar modelo
model = PoissonPropModel()

# Hacer predicción
line = 25.5  # Línea de la casa de apuestas

prediction = model.predict_value(
    mean=avg_points,    # 25.3
    std=std_points,     # 6.2
    line=line           # 25.5
)

# Resultados
prob_over = prediction['prob_over']     # Ej: 0.487 (48.7%)
prob_under = prediction['prob_under']   # Ej: 0.513 (51.3%)
predicted_value = prediction['predicted_value']  # 25.3
```

**¿Cómo funciona el modelo?**

El modelo Poisson asume que los puntos siguen una distribución de Poisson y calcula:
- La probabilidad de que el jugador haga **más** de X puntos (Over)
- La probabilidad de que el jugador haga **menos** de X puntos (Under)

---

### **PASO 4: Calcular Expected Value (EV)** 💎

```python
# Cuotas de la casa
odds_over = 1.90
odds_under = 1.90

# Convertir odds a probabilidad implícita
implied_prob_over = 1 / odds_over   # 0.526 (52.6%)
implied_prob_under = 1 / odds_under # 0.526 (52.6%)

# Calcular EV
ev_over = (prob_over * (odds_over - 1)) - (prob_under * 1)
ev_under = (prob_under * (odds_under - 1)) - (prob_over * 1)

# Convertir a porcentaje
ev_over_percent = ev_over * 100   # Ej: -3.2%
ev_under_percent = ev_under * 100 # Ej: +1.8%

print(f"EV Over:  {ev_over_percent:+.2f}%")
print(f"EV Under: {ev_under_percent:+.2f}%")
```

**¿Qué significa el EV?**

- **EV > 0**: Value bet (apuesta con valor)
- **EV = 0**: Cuota justa (no hay ventaja)
- **EV < 0**: Mala apuesta (la casa tiene ventaja)

**Regla de oro:** Solo apostar si EV > 5%

---

### **PASO 5: Generar Recomendación** ⭐

```python
# Umbral mínimo de EV
ev_threshold = 5.0

if ev_over_percent > ev_threshold:
    recommendation = "OVER"
    ev_value = ev_over_percent
    odds_value = odds_over
elif ev_under_percent > ev_threshold:
    recommendation = "UNDER"
    ev_value = ev_under_percent
    odds_value = odds_under
else:
    recommendation = "NO APOSTAR"

# Mostrar recomendación
if recommendation != "NO APOSTAR":
    print(f"🎯 RECOMENDACIÓN: {recommendation} {line}")
    print(f"   Cuota: {odds_value}")
    print(f"   EV: +{ev_value:.2f}%")
    print(f"   URL: {bookmaker_url}")
```

---

### **PASO 6: Guardar en Base de Datos** 💾

```python
from src.database import init_db, get_session, Pick

# Inicializar DB
engine = init_db()
session = get_session(engine)

# Crear pick
pick = Pick(
    match_id=1,
    market_type='points',
    player_name='LeBron James',
    selection='over',
    line=25.5,
    odds=1.95,
    bookmaker='williamhill',
    bookmaker_display_name='William Hill',
    betting_url='https://sports.williamhill.es/...',
    estimated_prob=0.55,
    expected_value=0.08,
    edge_percent=8.0,
    status='recommended',
    result='pending'
)

session.add(pick)
session.commit()

print(f"✓ Pick guardado (ID: {pick.id})")
```

---

## 📊 Ejemplo Completo

```python
#!/usr/bin/env python3
"""Ejemplo: Predecir puntos de LeBron James"""

from src.ingest.nba_scraper import NBAStatsScraper
from src.ingest.odds_collector import MultiBookCollector
from src.models.poisson_model import PoissonPropModel

# 1. STATS
scraper = NBAStatsScraper()
game_log = scraper.get_player_game_log("LeBron James", last_n_games=10)
avg = game_log['PTS'].mean()
std = game_log['PTS'].std()

# 2. ODDS
config = {'the_odds_api': {'enabled': True, 'api_key': 'tu_key'}}
collector = MultiBookCollector(config)
odds_data = collector.collect_all_odds(['nba'], ['player_points'])

# Extraer odds (simplificado)
line = 25.5
odds_over = 1.90

# 3. PREDICCIÓN
model = PoissonPropModel()
pred = model.predict_value(mean=avg, std=std, line=line)
prob_over = pred['prob_over']

# 4. EV
ev = (prob_over * (odds_over - 1)) - ((1 - prob_over) * 1)
ev_percent = ev * 100

# 5. RECOMENDACIÓN
if ev_percent > 5.0:
    print(f"✓ APOSTAR OVER {line} @ {odds_over}")
    print(f"  EV: +{ev_percent:.2f}%")
    print(f"  URL: {bookmaker_url}")
else:
    print("✗ NO APOSTAR - EV insuficiente")
```

---

## 🎮 Probar el Sistema

### Script de Ejemplo Completo

```bash
# Ejecutar ejemplo completo
python examples/example_hacer_prediccion.py
```

Este script muestra:
- ✅ Obtención de stats de NBA
- ✅ Obtención de odds con URLs
- ✅ Predicción con modelo
- ✅ Cálculo de EV
- ✅ Recomendación final
- ✅ Guardado en base de datos

### Ejemplo Rápido (sin API)

```bash
# En Python interactivo
python3

>>> from scipy.stats import norm
>>>
>>> # Datos
>>> avg = 25.3
>>> std = 6.2
>>> line = 25.5
>>> odds_over = 1.90
>>>
>>> # Predicción
>>> z = (line - avg) / std
>>> prob_under = norm.cdf(z)
>>> prob_over = 1 - prob_under
>>>
>>> # EV
>>> ev = (prob_over * (odds_over - 1)) - (prob_under * 1)
>>> print(f"Prob Over: {prob_over:.1%}")
>>> print(f"EV: {ev*100:+.2f}%")
```

---

## 📚 Modelos Disponibles

### 1. **Poisson Model** (Recomendado para baloncesto)
```python
from src.models.poisson_model import PoissonPropModel
model = PoissonPropModel()
```

**Mejor para:**
- Puntos de jugadores NBA/ACB
- Rebounds, asistencias
- Props con valores medios/altos

### 2. **Bayesian Model** (Para stats complejas)
```python
from src.models.bayesian_model import BayesianPropModel
model = BayesianPropModel()
```

**Mejor para:**
- Incorporar información previa
- Ajustar por contexto (home/away, rival)
- Stats con alta variabilidad

### 3. **Calibrated Model** (Más preciso)
```python
from src.models.calibration import calibrate_model
calibrated_model = calibrate_model(historical_data)
```

**Mejor para:**
- Después de tener datos históricos
- Ajustar los factores del modelo
- Mejorar precisión

---

## ⚙️ Configuración Necesaria

### 1. **API Keys**

En tu archivo `.env`:

```bash
# The Odds API (gratis: 500 requests/mes)
THE_ODDS_API_KEY=tu_key_aqui

# Base de datos (por defecto SQLite)
DATABASE_URL=sqlite:///data/results/sports_bot.db
```

### 2. **Instalar Dependencias**

```bash
# Instalar todo
pip install -r requirements.txt

# Solo para NBA
pip install nba-api

# Solo para modelos
pip install scipy numpy scikit-learn
```

### 3. **Inicializar Base de Datos**

```bash
# Crear tablas
python -c "from src.database import init_db; init_db()"
```

---

## 💡 Tips y Mejores Prácticas

### **1. Solo apostar con EV > 5%**
```python
ev_threshold = 5.0  # Mínimo 5% de ventaja
```

### **2. Kelly Criterion para el stake**
```python
edge = (prob * odds - 1) / (odds - 1)
kelly_stake = edge * bankroll
recommended_stake = kelly_stake * 0.25  # Quarter Kelly
```

### **3. Diversificar**
No apostar más del 5% del bankroll en una sola apuesta.

### **4. Tracking**
Guardar TODAS las apuestas en la DB para análisis posterior:
```python
session.add(pick)
session.commit()
```

### **5. CLV (Closing Line Value)**
Comparar tu apuesta con la línea de cierre:
```python
clv = (odds_closing - odds_placed) / odds_placed
```

---

## 🔧 Troubleshooting

### "Module not found: nba_api"
```bash
pip install nba-api
```

### "THE_ODDS_API_KEY no configurada"
1. Obtén key gratis en https://the-odds-api.com/
2. Añade en `.env`: `THE_ODDS_API_KEY=tu_key`

### "Error en base de datos"
```bash
# Inicializar DB
python -c "from src.database import init_db; init_db()"
```

### "No se encuentran odds"
- Verifica que THE_ODDS_API_KEY esté configurada
- Comprueba que el deporte esté disponible en The Odds API
- Revisa el rate limit (500 requests/mes gratis)

---

## 📖 Más Recursos

- **Documentación fuentes de datos**: `docs/FUENTES_DE_DATOS_Y_URLS.md`
- **Ejemplo odds con URLs**: `examples/example_odds_with_urls.py`
- **Script de predicción**: `examples/example_hacer_prediccion.py`
- **Main bot**: `src/main.py`

---

## 🎯 Workflow Recomendado

```
1. Cada mañana:
   - Ejecutar bot para obtener picks del día
   - Revisar recomendaciones con EV > 5%

2. Antes de apostar:
   - Verificar odds actuales (pueden cambiar)
   - Comprobar noticias (lesiones, descansos)
   - Confirmar lineups

3. Después del evento:
   - Actualizar resultados
   - Calcular CLV
   - Analizar performance del modelo

4. Semanalmente:
   - Revisar ROI
   - Ajustar parámetros si es necesario
   - Re-calibrar modelos
```

---

**¡Buena suerte con tus predicciones!** 🚀

Para más ayuda, consulta:
- GitHub Issues: https://github.com/pitiflautico/apuestas-bot/issues
- Documentación completa: `docs/`
