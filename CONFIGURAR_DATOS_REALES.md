# 🎯 Configurar Sistema para Datos REALES

## ✅ Resumen: ¿El sistema usa datos reales?

**SÍ**, el sistema **puede usar datos 100% reales**, pero necesitas configurarlo primero.

### 📊 Tipos de Datos

1. **Estadísticas** (Stats de jugadores/equipos):
   - ✅ NBA → `nba_api` (datos oficiales de NBA.com)
   - ✅ EuroLeague → SofaScore API (datos en vivo)
   - ✅ Soccer → SofaScore + FBref (datos reales)
   - ✅ Tennis → SofaScore API (datos reales)

2. **Cuotas** (Odds de casas de apuestas):
   - ✅ The Odds API → Cuotas EN VIVO de 8+ bookmakers
   - ✅ Bet365, Pinnacle, William Hill, Betfair, etc.

3. **URLs** (Enlaces a casas para apostar):
   - ✅ Ya configuradas en `config/books.yaml`
   - ✅ 8 bookmakers con URLs directas

### ⚠️ Estado Actual (según test)

```bash
❌ No hay archivo .env configurado
❌ THE_ODDS_API_KEY no configurada
❌ Dependencias no instaladas (nba-api, pandas, etc.)
✅ URLs de bookmakers funcionan
```

**Conclusión**: El sistema está PREPARADO para datos reales, pero **NO configurado**.

---

## 🚀 Configuración en 3 Pasos (15 minutos)

### **PASO 1: Instalar Dependencias**

```bash
# Método 1: Auto-instalador (Recomendado)
./install.sh

# Método 2: Manual
pip install -r requirements.txt
pip install nba-api cloudscraper pandas numpy scipy pyyaml
```

### **PASO 2: Obtener API Key (GRATIS)**

1. **Registrarse** en: https://the-odds-api.com/
2. Click en "**Get API Key**"
3. **Confirmar email** que te envían
4. **Copiar tu API key** desde: https://the-odds-api.com/account/

📋 **Plan Gratis**:
- ✅ 500 requests/mes (suficiente para uso normal)
- ✅ Todos los deportes y mercados
- ✅ Datos en tiempo real

### **PASO 3: Configurar .env**

Edita el archivo `.env`:

```bash
# Abre el archivo
nano .env

# O con cualquier editor
code .env
```

Añade tu API key:

```bash
# API Keys para datos reales
THE_ODDS_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6  # ← Tu key aquí

# Database
DATABASE_URL=sqlite:///data/results/sports_bot.db

# Logging
LOG_LEVEL=INFO
```

**¡IMPORTANTE!** Reemplaza `a1b2c3d4e5f6...` por tu API key real.

---

## 🧪 Verificar Configuración

Ejecuta el test de verificación:

```bash
python test_datos_reales.py
```

**Resultado esperado:**

```
✅ Archivo .env encontrado
✅ THE_ODDS_API_KEY configurada: a1b2c3d4...

--- Test 1: NBA Stats (Datos Reales) ---
✅ NBA API funciona - 5 partidos obtenidos
   Último partido: 2024-11-08 - 28 puntos
   → DATOS REALES ✅

--- Test 2: Odds API (Cuotas Reales) ---
✅ The Odds API funciona - 10 partidos obtenidos
   Partido: Barcelona vs Real Madrid
   Casas: 6 bookmakers con cuotas
   → CUOTAS REALES ✅

--- Test 3: Bookmaker URLs (URLs Reales) ---
✅ URLs de casas configuradas
   Bet365 NBA: https://www.bet365.es/...
   → URLs REALES ✅
```

Si ves ✅ en todo → **¡Sistema listo con datos reales!** 🎉

---

## 🎮 Probar el Sistema con Datos Reales

### Opción 1: Ejemplo Completo

```bash
python examples/example_hacer_prediccion.py
```

Este script hace una predicción REAL:
1. Obtiene stats reales de LeBron James (NBA API)
2. Obtiene cuotas reales (The Odds API)
3. Calcula probabilidad (modelo Poisson)
4. Calcula Expected Value
5. Recomienda apuesta si EV > 5%
6. Muestra URL directa a la casa de apuestas

### Opción 2: Consulta Rápida de Odds

```bash
python examples/example_odds_with_urls.py
```

Muestra:
- ✅ Cuotas actuales de todos los partidos de hoy
- ✅ URLs directas a cada casa de apuestas
- ✅ Comparación de odds entre bookmakers

### Opción 3: Script Manual

```python
from src.ingest.odds_collector import MultiBookCollector

config = {
    'the_odds_api': {
        'enabled': True,
        'api_key': 'tu_api_key_aqui'  # Desde .env
    }
}

collector = MultiBookCollector(config)

# Obtener odds EN VIVO
odds = collector.collect_all_odds(
    sports=['nba', 'euroleague', 'laliga'],
    markets=['h2h', 'totals']
)

# Ver partidos con URLs
for event in odds['nba']:
    print(f"{event['home_team']} vs {event['away_team']}")

    for bookmaker in event['bookmakers']:
        print(f"  {bookmaker['display_name']}: {bookmaker['betting_url']}")
```

---

## 🔍 Cómo Saber si Estás Usando Datos Reales

### ✅ Señales de Datos REALES:

1. **Fechas actuales**: Partidos de hoy/esta semana
   ```
   Partido: Lakers vs Warriors
   Fecha: 2024-11-09  ← HOY
   ```

2. **Jugadores actuales**: Stats de jugadores activos
   ```
   LeBron James - Último partido: 2024-11-08
   Puntos: 28  ← Dato real del partido de ayer
   ```

3. **Cuotas cambiantes**: Las odds varían ligeramente cada vez
   ```
   Primera consulta:  Over 25.5 @ 1.90
   5 minutos después: Over 25.5 @ 1.87  ← Cambió
   ```

4. **Rate limit messages**: The Odds API te informa de tu uso
   ```
   Rate limit remaining: 487  ← Consumiste 13 requests
   ```

### ❌ Señales de Datos SIMULADOS:

1. **Fechas antiguas/genéricas**: "2024-01-01"
2. **Stats redondos sospechosos**: 25.0 puntos exactos cada partido
3. **Cuotas que no cambian**: Siempre 1.90 exacto
4. **Warnings en consola**:
   ```
   ⚠️ Usando datos simulados para demostración
   ⚠️ THE_ODDS_API_KEY no configurada
   ```

---

## 💰 Consumo de API Requests

### ¿Cuántos requests consume cada acción?

| Acción | Requests | Ejemplo |
|--------|----------|---------|
| Obtener odds de 1 deporte × 1 mercado | 1 | NBA h2h = 1 |
| Obtener odds de 1 deporte × 3 mercados | 3 | NBA (h2h + totals + props) = 3 |
| Ejecutar `example_hacer_prediccion.py` | 1-3 | Depende de mercados |
| Bot completo diario | ~10 | NBA + EuroLeague + La Liga |

### Plan de Consumo Mensual:

```
Uso conservador (1 vez al día):
- NBA (h2h, totals, props): 3 requests
- EuroLeague (h2h, totals): 2 requests
- La Liga (h2h): 1 request
= 6 requests/día × 30 días = 180 requests/mes

→ Plan gratis (500/mes) es MÁS que suficiente ✅

Uso intensivo (3 veces al día):
= 6 × 3 = 18 requests/día × 30 = 540 requests/mes

→ Necesitarías plan pago ($59/mes) o reducir frecuencia
```

### Tips para Ahorrar Requests:

1. **Cachear resultados**: Guardar odds en DB, reutilizar durante 15-30 min
2. **Consultar solo deportes activos**: No consultar NBA en verano
3. **Agrupar mercados**: `markets=['h2h','totals','spreads']` en 1 request
4. **Filtrar por fecha**: Solo partidos de hoy/mañana

---

## 🐛 Troubleshooting

### Error: "Module not found: nba_api"
```bash
pip install nba-api
```

### Error: "THE_ODDS_API_KEY no configurada"
1. Verifica que `.env` existe en la raíz del proyecto
2. Comprueba que la key no tiene espacios ni comillas
3. Reinicia el script/terminal después de editar .env

### Error: "401 Unauthorized" (The Odds API)
- API key incorrecta
- Verifica en: https://the-odds-api.com/account/

### Error: "429 Rate Limit Exceeded"
- Estás haciendo más de 10 requests/minuto
- Añade `time.sleep(6)` entre requests

### Error: "403 Quota Exceeded"
- Has superado 500 requests este mes
- Espera al próximo mes o actualiza a plan pago
- Consulta uso en: https://the-odds-api.com/account/

### No se obtienen odds (lista vacía)
- Normal si no hay partidos programados para hoy
- Prueba con diferentes deportes:
  ```python
  odds = collector.collect_all_odds(['laliga'])  # Siempre hay partidos
  ```

---

## 📚 Archivos Útiles

```
.env                              # ← Configurar API keys aquí
config/books.yaml                 # URLs de bookmakers
test_datos_reales.py              # Verificar configuración
COMO_OBTENER_API_KEY.md          # Guía para obtener API key

examples/
  example_hacer_prediccion.py     # Predicción completa
  example_odds_with_urls.py       # Solo odds con URLs

docs/
  COMO_HACER_PREDICCIONES.md     # Tutorial paso a paso
  FUENTES_DE_DATOS_Y_URLS.md     # Documentación de datos
```

---

## ✅ Checklist de Configuración

```
[ ] Instalar dependencias (./install.sh)
[ ] Obtener THE_ODDS_API_KEY gratis
[ ] Configurar .env con la API key
[ ] Ejecutar test_datos_reales.py → Ver ✅
[ ] Probar example_hacer_prediccion.py
[ ] Verificar que las fechas son actuales
[ ] Verificar que las odds cambian
[ ] ¡Listo para hacer predicciones reales!
```

---

## 🎯 ¿Cuándo Usar Datos Reales vs Simulados?

### Datos REALES (Producción):
- ✅ Hacer apuestas de verdad
- ✅ Backtesting con datos históricos reales
- ✅ Calibrar modelos
- ✅ Análisis de ROI

### Datos SIMULADOS (Solo para):
- ⚠️ Aprender cómo funciona el código
- ⚠️ Testear cambios en el código
- ⚠️ Cuando no tienes API key configurada

**NUNCA** hagas apuestas reales con datos simulados.

---

## 📞 Soporte

Si tienes problemas:

1. **Ejecuta el test**: `python test_datos_reales.py`
2. **Lee los errores**: Los mensajes indican qué falta
3. **Consulta docs**: `COMO_OBTENER_API_KEY.md`
4. **GitHub Issues**: https://github.com/pitiflautico/apuestas-bot/issues

---

**¡Buena suerte con tus predicciones REALES!** 🚀

Recuerda:
- Solo apostar con EV > 5%
- Usar Kelly Criterion para stakes
- Trackear TODAS las apuestas
- Revisar CLV (Closing Line Value)
