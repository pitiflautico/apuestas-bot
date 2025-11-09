# Fuentes de Datos Históricos

## 🏀 NBA (Basketball)

### Stats API (Oficial - FREE)
- **API**: `nba_api` (Python package)
- **Datos**: Temporadas completas desde 1996
- **Incluye**:
  - Game logs de jugadores (puntos, rebotes, asistencias, minutos)
  - Stats de equipos (pace, defensive rating)
  - Splits (home/away, vs opponent)
- **Limitaciones**: Rate limit ~60 req/min
- **Setup**: `pip install nba-api`

```python
from nba_api.stats.endpoints import playergamelog

# Obtener últimos 20 partidos de LeBron James
game_log = playergamelog.PlayerGameLog(
    player_id=2544,  # LeBron's ID
    season='2024-25'
)
df = game_log.get_data_frames()[0]
```

### Basketball-Reference (Web Scraping)
- **URL**: https://www.basketball-reference.com/
- **Datos**: Históricos completos desde 1947
- **Método**: Web scraping con `pandas.read_html()`
- **Rate Limit**: 20 req/min (respetar robots.txt)

---

## 🏀 ACB (Liga Endesa - España)

### SofaScore API (Público - FREE)
- **API**: https://api.sofascore.com/api/v1
- **Datos**: Temporadas recientes (2018+)
- **Incluye**:
  - Stats de jugadores por partido
  - Stats de equipos
  - Calendario completo
- **Limitaciones**: Rate limit ~30 req/min
- **Método**: HTTP requests directos

```python
import requests

# Obtener partidos de un equipo ACB
url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/10"
response = requests.get(url)
matches = response.json()
```

### ACB.com (Web Scraping)
- **URL**: http://www.acb.com/
- **Datos**: Estadísticas oficiales ACB
- **Método**: Web scraping (requiere análisis de estructura)
- **Calidad**: Stats oficiales muy completas

---

## ⚽ La Liga (Fútbol)

### FBref (FREE - Web Scraping)
- **URL**: https://fbref.com/
- **Datos**: Stats avanzadas desde 2017
- **Incluye**:
  - Corners, shots, cards por equipo y partido
  - xG (expected goals)
  - Stats de jugadores
- **Método**: `pandas.read_html()` + BeautifulSoup
- **Rate Limit**: 20 req/min

```python
import pandas as pd

# La Liga 2024-25
url = "https://fbref.com/en/comps/12/La-Liga-Stats"
tables = pd.read_html(url)
team_stats = tables[0]
```

### SofaScore API (FREE)
- **API**: https://api.sofascore.com/api/v1
- **Datos**: Partidos recientes con stats detalladas
- **Incluye**: Corners, shots, cards, fouls

### Understat (xG Data)
- **URL**: https://understat.com/
- **Datos**: Expected Goals (xG) desde 2014
- **Método**: Web scraping

---

## 🎾 Tennis (ATP/WTA)

### SofaScore API (FREE)
- **API**: https://api.sofascore.com/api/v1
- **Datos**: Partidos recientes ATP/WTA
- **Incluye**: Aces, double faults, service stats

### Tennis Abstract (FREE)
- **URL**: http://www.tennisabstract.com/
- **Datos**: Stats históricos completos
- **Incluye**:
  - Aces, double faults por superficie
  - Head-to-head
  - Service stats detallados
- **Método**: Web scraping + CSV downloads

### ATP/WTA Official APIs (Limitado)
- **URLs**:
  - ATP: https://www.atptour.com/
  - WTA: https://www.wta.com/
- **Datos**: Stats oficiales
- **Método**: Web scraping (sin API pública completa)

---

## 📊 Datos de Cuotas Históricas

### Odds Portal (FREE con limitaciones)
- **URL**: https://www.oddsportal.com/
- **Datos**: Histórico de cuotas de múltiples bookmakers
- **Incluye**: Líneas de cierre (closing lines)
- **Método**: Web scraping (requiere navegación)
- **Importante**: Para calcular CLV

### Pinnacle (Sharp Book)
- **Datos**: Cuotas históricas si tienes cuenta
- **Uso**: Benchmark para "fair odds"

---

## 🔧 Métodos de Obtención

### 1. APIs Públicas (Recomendado)
```python
# NBA API - Directo
from nba_api.stats.endpoints import playergamelog

# SofaScore - HTTP requests
import requests
response = requests.get(sofascore_url)
data = response.json()
```

### 2. Web Scraping
```python
# FBref con pandas
import pandas as pd
tables = pd.read_html(url)

# BeautifulSoup para HTML complejo
from bs4 import BeautifulSoup
import requests

response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')
```

### 3. Bases de Datos Comerciales (Paid)
- **Sportradar**: API completa multi-deporte
- **Opta Sports**: Stats oficiales de ligas
- **StatsPerform**: Datos profesionales

---

## 📅 Cantidad de Datos Recomendada

### Para Calibración Inicial:
- **Mínimo**: 1 temporada completa (~80 partidos por equipo/jugador)
- **Recomendado**: 2-3 temporadas (para capturar diferentes contextos)

### Para Modelos ML:
- **Mínimo**: 1000 partidos
- **Óptimo**: 5000+ partidos

### Para Props de Jugador:
- **Mínimo por jugador**: 20 partidos
- **Óptimo**: 50+ partidos (o 2 temporadas)

---

## ⚠️ Consideraciones Legales

### Rate Limiting
- **Respetar** los límites de cada fuente
- Usar delays entre requests (1-3 segundos)
- Cachear datos localmente

### Terms of Service
- ✅ NBA API: Libre para uso personal/educativo
- ✅ FBref: Scraping permitido con rate limits
- ⚠️ SofaScore: API no oficial, usar responsablemente
- ❌ Comercial: Requiere licencias (Opta, Sportradar)

### Ejemplo de Rate Limiting:
```python
import time

for game in games:
    fetch_data(game)
    time.sleep(2)  # 2 segundos entre requests
```

---

## 🚀 Scripts de Descarga Incluidos

El proyecto incluye scripts automatizados:

```bash
# Descargar datos históricos de NBA
python scripts/download_nba_history.py --seasons 2022-23 2023-24 2024-25

# Descargar datos de La Liga
python scripts/download_laliga_history.py --season 2024-25

# Descargar datos de Tennis
python scripts/download_tennis_history.py --tour atp --year 2024

# Poblar base de datos completa
python scripts/populate_historical_data.py
```

---

## 💡 Recomendaciones

1. **Empezar con NBA**: API oficial muy completa y fácil
2. **Cachear datos**: No descargar lo mismo varias veces
3. **Incremental updates**: Solo actualizar partidos nuevos
4. **Backup**: Guardar CSVs de respaldo
5. **Validar**: Verificar calidad de datos descargados

---

## 📦 Estructura de Almacenamiento

```
data/
├── raw/                    # Datos crudos de APIs
│   ├── nba/
│   │   ├── 2024-25/
│   │   │   ├── player_gamelogs/
│   │   │   └── team_stats/
│   ├── acb/
│   ├── laliga/
│   └── tennis/
├── curated/               # Datos procesados
│   ├── nba_player_stats.parquet
│   ├── laliga_team_stats.parquet
│   └── tennis_match_stats.parquet
└── results/
    └── sports_bot.db     # Base de datos SQLite
```

---

## 🔄 Pipeline de Actualización

```
1. Daily: Actualizar odds actuales (The Odds API)
2. Daily: Actualizar resultados de ayer
3. Weekly: Actualizar stats de jugadores/equipos
4. Monthly: Re-calibrar modelos
```
