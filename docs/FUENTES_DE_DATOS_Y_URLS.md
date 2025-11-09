# Fuentes de Datos y URLs a Casas de Apuestas

## 📊 ¿De Dónde Vienen los Datos?

### 1. **Estadísticas Deportivas** (Stats)

Usamos fuentes oficiales y públicas para obtener estadísticas de jugadores/equipos:

#### 🏀 NBA
- **Fuente**: NBA API Oficial (`nba-api` package)
- **Datos**:
  - Game logs de jugadores (puntos, rebotes, asistencias, minutos)
  - Stats de equipos (pace, defensive rating)
  - Histórico completo desde 1996
- **Archivos**: `src/ingest/nba_scraper.py`

#### 🏀 ACB (Liga Endesa)
- **Fuente**: SofaScore API Pública
- **Datos**:
  - Stats de jugadores por partido
  - Stats de equipos
  - Calendario y resultados
- **Archivos**: `src/ingest/acb_scraper.py`

#### ⚽ La Liga (Fútbol)
- **Fuentes**:
  - FBref (stats avanzadas)
  - SofaScore API
- **Datos**:
  - Corners, shots, cards por equipo
  - Expected goals (xG)
  - Stats de jugadores
- **Archivos**: `src/ingest/soccer_scraper.py`

#### 🎾 Tenis (ATP/WTA)
- **Fuentes**:
  - SofaScore API
  - Tennis Abstract
- **Datos**:
  - Aces, double faults
  - Service stats
  - Histórico por superficie
- **Archivos**: `src/ingest/tennis_scraper.py`

---

### 2. **Cuotas de Casas de Apuestas** (Odds)

Las cuotas se obtienen de **The Odds API**, que agrega datos de múltiples bookmakers:

#### The Odds API
- **URL**: https://the-odds-api.com/
- **Plan Gratuito**: 500 requests/mes
- **Bookmakers incluidos**:
  - Bet365
  - William Hill
  - Pinnacle
  - Betfair
  - Codere
  - Bwin
  - Marathon Bet
  - Unibet
  - Y más...

#### Configuración
```bash
# En .env
THE_ODDS_API_KEY=tu_api_key_aqui
```

#### Uso
```python
from src.ingest.odds_collector import MultiBookCollector

config = {
    'the_odds_api': {
        'enabled': True,
        'api_key': 'tu_api_key'
    }
}

collector = MultiBookCollector(config)
odds = collector.collect_all_odds(
    sports=['nba'],
    markets=['player_points', 'player_rebounds']
)
```

---

## 🔗 URLs Directas a las Apuestas

### ¿Cómo Funciona?

El sistema **automáticamente** añade URLs directas a las casas de apuestas:

1. **Configuración**: Las URLs están en `config/books.yaml`
2. **Enriquecimiento**: Cuando se obtienen odds, se añaden las URLs
3. **Resultado**: Cada odd tiene su URL directa para apostar

### Ejemplo de Resultado

```python
{
    "home_team": "Lakers",
    "away_team": "Warriors",
    "bookmakers": [
        {
            "key": "bet365",
            "display_name": "Bet365",
            "betting_url": "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/",
            "markets": [
                {
                    "key": "player_points",
                    "outcomes": [
                        {"name": "LeBron Over 25.5", "price": 1.90},
                        {"name": "LeBron Under 25.5", "price": 1.90}
                    ]
                }
            ]
        },
        {
            "key": "williamhill",
            "display_name": "William Hill",
            "betting_url": "https://sports.williamhill.es/betting/es-es/baloncesto/competiciones/NBA",
            "markets": [...]
        }
    ]
}
```

---

## 🏆 Casas de Apuestas Configuradas

### España (Licencia DGOJ)

| Casa | URL | Deportes | Notas |
|------|-----|----------|-------|
| **Bet365** | https://www.bet365.es/ | NBA, ACB, La Liga, Tenis | Más popular en España |
| **William Hill** | https://sports.williamhill.es/ | NBA, ACB, La Liga, Tenis | Buenas cuotas |
| **Codere** | https://www.codere.es/deportes | NBA, ACB, La Liga, Tenis | Licencia española |
| **Bwin** | https://sports.bwin.es/ | NBA, ACB, La Liga, Tenis | Amplio mercado |
| **Marathon Bet** | https://www.marathonbet.es/ | NBA, La Liga, Tenis | Buenas cuotas |
| **Unibet** | https://www.unibet.es/ | NBA, ACB, La Liga, Tenis | Interface moderna |

### Internacional

| Casa | URL | Deportes | Notas |
|------|-----|----------|-------|
| **Pinnacle** | https://www.pinnacle.com/en/ | NBA, La Liga, Tenis | Sharp book (para CLV) |
| **Betfair** | https://www.betfair.com/exchange/plus/ | NBA, La Liga, Tenis | Exchange (sin comisión fija) |

---

## 📝 Configuración de URLs

### Archivo: `config/books.yaml`

```yaml
bookmakers:
  bet365:
    name: "Bet365"
    url: "https://www.bet365.es/"
    betting_urls:
      basketball: "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/"
      basketball_nba: "https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/"
      soccer: "https://www.bet365.es/#/AC/B1/C1/D13/E169/F2/"
      tennis: "https://www.bet365.es/#/AC/B5/C1/D13/E168/F2/"
    the_odds_api_key: "bet365"
```

### Añadir Nueva Casa

1. Edita `config/books.yaml`
2. Añade la configuración:
```yaml
  nueva_casa:
    name: "Nueva Casa"
    url: "https://www.nuevacasa.es/"
    betting_urls:
      basketball_nba: "https://www.nuevacasa.es/nba"
      soccer_laliga: "https://www.nuevacasa.es/laliga"
    the_odds_api_key: "nuevacasa"  # Key de The Odds API
```

---

## 🚀 Ejemplo Práctico

### Script de Demostración

```bash
# Ejecutar ejemplo completo
python examples/example_odds_with_urls.py
```

Este script muestra:
- ✅ Todas las casas de apuestas disponibles
- ✅ URLs directas para cada deporte
- ✅ Cómo obtener odds con URLs
- ✅ Comparación de cuotas entre casas
- ✅ Dónde hacer cada apuesta

### Salida del Script

```
🏀 Lakers vs Warriors
   Fecha: 2025-11-10T02:00:00Z

   📍 Casas de Apuestas con URLs Directas:

   ✓ Bet365
     🔗 URL: https://www.bet365.es/#/AC/B3/C20604387/D48/E174/F48/
     📊 Mercado: player_points
        - LeBron James Over 25.5: 1.90
        - LeBron James Under 25.5: 1.90

   ✓ William Hill
     🔗 URL: https://sports.williamhill.es/betting/es-es/baloncesto/competiciones/NBA
     📊 Mercado: player_points
        - LeBron James Over 25.5: 1.95 ⭐ MEJOR
        - LeBron James Under 25.5: 1.85

   🎯 RECOMENDACIÓN:
   Si quieres apostar OVER 25.5:
     ✓ Casa: William Hill
     ✓ Cuota: 1.95
     ✓ URL: https://sports.williamhill.es/betting/es-es/baloncesto/competiciones/NBA
```

---

## 💾 Base de Datos

Las URLs se guardan en la base de datos:

### Tabla `odds`
```sql
CREATE TABLE odds (
    id INTEGER PRIMARY KEY,
    match_id INTEGER,
    bookmaker VARCHAR(100),
    bookmaker_display_name VARCHAR(200),  -- "Bet365", "William Hill"
    bookmaker_url VARCHAR(500),            -- URL directa
    market_type VARCHAR(100),
    player_name VARCHAR(200),
    line FLOAT,
    over_odds FLOAT,
    under_odds FLOAT,
    ...
);
```

### Tabla `picks`
```sql
CREATE TABLE picks (
    id INTEGER PRIMARY KEY,
    match_id INTEGER,
    market_type VARCHAR(100),
    player_name VARCHAR(200),
    bookmaker VARCHAR(100),
    bookmaker_display_name VARCHAR(200),   -- "Bet365"
    betting_url VARCHAR(500),               -- URL directa para apostar
    odds FLOAT,
    expected_value FLOAT,
    ...
);
```

---

## 🔄 Flujo de Datos Completo

```
1. STATS
   ├─ NBA API ────────┐
   ├─ SofaScore ──────┤
   ├─ FBref ──────────┤
   └─ Tennis Abstract ┘
          │
          ▼
   [PlayerStats DB]

2. ODDS + URLs
   The Odds API ────┐
          │         │
          ▼         │
   [Odds Collector] │
          │         │
          ▼         │
   BookmakerURLBuilder ← config/books.yaml
          │
          ▼
   [Odds DB con URLs]

3. PREDICCIÓN
   [PlayerStats] + [Odds]
          │
          ▼
   [Modelos ML]
          │
          ▼
   [Predictions DB]

4. VALUE BET
   [Predictions] + [Odds con URLs]
          │
          ▼
   [EV Calculator]
          │
          ▼
   [Picks DB con URLs] ──┐
          │              │
          ▼              │
   [Dashboard] ─────────┘
          │
          ▼
   Usuario ve:
   - Apuesta recomendada
   - Cuota y casa
   - URL DIRECTA para apostar
```

---

## ❓ Preguntas Frecuentes

### ¿Necesito cuenta en todas las casas?
No, el bot te muestra las cuotas de todas, pero tú decides en cuál apostar.

### ¿Las URLs son enlaces de afiliado?
No, son enlaces directos a las secciones de deportes. Puedes modificarlas en `config/books.yaml`.

### ¿Puedo añadir más casas?
Sí, edita `config/books.yaml` y añade las URLs. Asegúrate de que The Odds API tenga datos de esa casa.

### ¿Qué pasa si una casa no está en The Odds API?
Solo se mostrarán las casas que The Odds API soporta. Puedes ver la lista completa en:
https://the-odds-api.com/sports-odds-data/bookmaker-apis.html

### ¿Cómo actualizo las URLs si cambian?
Edita `config/books.yaml` y actualiza las URLs. El sistema las usará automáticamente.

---

## 🛠️ Archivos Importantes

```
apuestas-bot/
├── config/
│   └── books.yaml                    # ⭐ URLs de casas de apuestas
├── src/
│   ├── ingest/
│   │   ├── odds_collector.py        # ⭐ Obtiene odds + añade URLs
│   │   ├── nba_scraper.py           # Stats NBA
│   │   ├── acb_scraper.py           # Stats ACB
│   │   ├── soccer_scraper.py        # Stats La Liga
│   │   └── tennis_scraper.py        # Stats Tenis
│   └── database.py                   # ⭐ Modelos con URLs
├── examples/
│   └── example_odds_with_urls.py    # ⭐ Ejemplo completo
└── docs/
    ├── DATA_SOURCES.md              # Fuentes de datos stats
    └── FUENTES_DE_DATOS_Y_URLS.md   # ⭐ Este archivo
```

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que `THE_ODDS_API_KEY` esté en `.env`
2. Revisa `config/books.yaml` para ver las URLs disponibles
3. Ejecuta `python examples/example_odds_with_urls.py` para probar
4. Consulta los logs para errores

---

**Última actualización**: 2025-11-09
