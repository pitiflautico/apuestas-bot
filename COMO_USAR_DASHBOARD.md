# 📊 Cómo Usar el Dashboard (DATOS REALES)

## 🎯 Nuevo Dashboard Mejorado

El dashboard ahora está **conectado a datos reales** con controles de riesgo completos.

---

## 🚀 Iniciar el Dashboard

```bash
# 1. Asegúrate de tener dependencias instaladas
pip install streamlit plotly pandas sqlalchemy

# 2. Lanzar el dashboard
streamlit run app.py

# Se abrirá en: http://localhost:8501
```

---

## ✨ Características Principales

### 1. **Controles de Riesgo en Sidebar** ⚠️

El sidebar izquierdo tiene todos los controles de riesgo:

#### **Minimum EV %** (Default: 5%)
- **Qué hace**: Filtra picks con Expected Value mínimo
- **Ejemplo**:
  - EV 3% → Muestra picks con >3% de ventaja
  - EV 8% → Solo picks muy selectivos

#### **Kelly Fraction** (Default: 0.25 = Quarter Kelly)
- **Qué hace**: Ajusta el tamaño de apuestas
- **Ejemplo**:
  - 0.25 → Conservador (recomendado)
  - 0.50 → Moderado
  - 1.00 → Agresivo (Full Kelly - NO recomendado)

#### **Max Stake %** (Default: 5%)
- **Qué hace**: Límite máximo por apuesta
- **Ejemplo**:
  - 5% → Máximo 5% del bankroll por pick
  - 10% → Más agresivo (riesgo mayor)

#### **Odds Range** (Default: 1.7 - 2.5)
- **Qué hace**: Filtra por rango de cuotas
- **Ejemplo**:
  - 1.7-2.5 → Cuotas medias (más consistentes)
  - 1.5-5.0 → Todas las cuotas

---

### 2. **Filtros por Deporte** 🏆

Selecciona los deportes que quieres ver:

```
✅ 🏀 NBA
✅ 🏀 EuroLeague
✅ ⚽ La Liga
✅ 🎾 Tennis
```

**Ejemplo**: Si solo quieres ver NBA y EuroLeague, desmarca La Liga y Tennis.

---

### 3. **Rango de Fechas** 📅

Filtra picks por fecha:
- Default: Hoy + próximos 3 días
- Puedes ajustar a cualquier rango

---

### 4. **Botones de Acción** 🔄

#### **🔄 Refresh Data**
- Recarga datos del dashboard
- Usa después de generar nuevas predicciones

#### **🎯 Generate New Predictions**
- Muestra comandos para generar picks
- Usa los controles de riesgo actuales

---

## 📋 Tabs del Dashboard

### **Tab 1: 🎯 Today** (Principales Picks)

**Qué muestra**:
- Tabla de picks con **datos reales de la base de datos**
- Ordenados por EV (mayor a menor)
- **Enlaces clickeables** a casas de apuestas (🔗)

**Columnas**:
| Columna | Descripción | Ejemplo |
|---------|-------------|---------|
| Player/Team | Jugador o equipo | LeBron James |
| Market | Tipo de apuesta | Points |
| Selection | Over/Under | OVER |
| Line | Línea | 25.5 |
| Odds | Cuota | 1.90 |
| EV % | Expected Value | 6.2% |
| Model Prob | Probabilidad del modelo | 58.3% |
| Adjusted Stake % | Stake ajustado (Kelly × Fraction) | 2.8% |
| Bookmaker Link | Casa de apuestas (CLICKEABLE) | Bet365 🔗 |

**Códigos de color**:
- 🟢 Verde: EV > 8% (EXCELENTE)
- 🟡 Amarillo: EV 5-8% (BUENO)
- 🟠 Naranja: EV 3-5% (ACEPTABLE)

**Métricas resumen**:
- Total Picks: Número de picks
- Avg EV: EV promedio
- High EV Picks: Picks con >8% EV
- Total Exposure: % total del bankroll en juego

**Detalles expandibles**:
- Click en cada pick para ver análisis completo
- Incluye **enlace directo** a la casa de apuestas

---

### **Tab 2: 🏀 Matches** (Partidos)

**Qué muestra**:
- Próximos partidos
- Props disponibles por partido
- Top 5 picks por partido

**Ejemplo**:
```
⏰ 2024-11-09 20:00 - Lakers vs Warriors (12 props)
  [Expandir para ver picks]

  LeBron James - Points
  OVER 25.5 @ 1.90
  EV: +6.2%
  Bet365 [🔗 Bet]
```

---

### **Tab 3: 📈 Markets** (Mercados y Odds)

**Qué muestra**:
- Comparación de odds entre casas
- Últimas 24h de datos
- Mejor cuota disponible por mercado

**Uso**:
- Verificar si tienes las mejores odds
- Comparar casas antes de apostar

---

### **Tab 4: 📊 Historical** (Rendimiento)

**Qué muestra**:
- **ROI real** de tus picks cerrados
- **Win rate** (% ganadas)
- **P&L** en unidades
- Rendimiento por tipo de mercado

**Períodos disponibles**:
- Last 7 Days
- Last 30 Days
- Last 90 Days
- All Time

**Métricas**:
- Total Picks: Cuántas apuestas hiciste
- ROI: Return on Investment (%)
- Win Rate: % de apuestas ganadas
- P&L: Profit/Loss en unidades

---

### **Tab 5: ⚙️ Config** (Configuración)

**Qué muestra**:
- Estado de APIs
- Contadores de BD
- Comandos útiles

**Info mostrada**:
```
✅ The Odds API: Configured
   Key: a1b2c3d4...ef89

✅ Database: Connected
   Total Picks in DB: 47
   Total Matches in DB: 12
```

**Comandos rápidos**:
```bash
# Colectar odds
python scripts/collect_data.py

# Generar predicciones
python scripts/run_predictions.py

# Actualizar resultados
python scripts/update_results.py
```

---

### **Tab 6: 🚨 Alerts** (Alertas)

**Estado**: 🚧 En desarrollo

Futuras funciones:
- Telegram alerts
- Email notifications
- Injury tracking
- Line movement alerts

---

## 🎮 Workflow Completo

### **Uso Diario Típico**

```bash
# MAÑANA (9:00 AM)
# 1. Colectar odds del día
python scripts/collect_data.py

# 2. Generar predicciones
python scripts/run_predictions.py

# 3. Abrir dashboard
streamlit run app.py

# 4. Ajustar controles de riesgo en sidebar
#    - EV mínimo: 5%
#    - Kelly: 0.25
#    - Max stake: 5%

# 5. Ver picks en tab "Today"

# 6. Para cada pick:
#    a. Click en el pick para expandir detalles
#    b. Revisar análisis
#    c. Click en "🔗 Bet Now" para ir a la casa
#    d. Colocar apuesta MANUALMENTE

# NOCHE (11:00 PM)
# 7. Actualizar resultados
python scripts/update_results.py

# 8. Ver rendimiento en tab "Historical"
```

---

## 💡 Ejemplos de Uso

### **Ejemplo 1: Usuario Conservador**

**Objetivo**: Pocas apuestas, muy selectivas

**Settings en sidebar**:
```
Minimum EV %: 8%
Kelly Fraction: 0.20
Max Stake %: 3%
Odds Range: 1.7 - 2.2
Sports: Solo NBA
```

**Resultado esperado**: 2-5 picks/día con alta confianza

---

### **Ejemplo 2: Usuario Moderado**

**Objetivo**: Balance entre volumen y calidad

**Settings en sidebar**:
```
Minimum EV %: 5%
Kelly Fraction: 0.25
Max Stake %: 5%
Odds Range: 1.7 - 2.5
Sports: NBA + EuroLeague
```

**Resultado esperado**: 5-10 picks/día

---

### **Ejemplo 3: Usuario Agresivo**

**Objetivo**: Máximo volumen (NO recomendado para principiantes)

**Settings en sidebar**:
```
Minimum EV %: 3%
Kelly Fraction: 0.35
Max Stake %: 7%
Odds Range: 1.5 - 3.0
Sports: Todos
```

**Resultado esperado**: 10-20 picks/día

⚠️ **Advertencia**: Más picks = mayor varianza = mayor riesgo

---

## 🔗 Enlaces a Casas de Apuestas

### **Cómo Funcionan**

Los picks tienen **enlaces directos** a las casas de apuestas:

**En la tabla principal**:
```
Bookmaker Link: Bet365 🔗
```
→ Click para ir directamente a Bet365

**En detalles expandidos**:
```
🔗 Bet Now at William Hill
```
→ Click para ir al mercado específico

**URLs configuradas** (en `config/books.yaml`):
- Bet365 → https://www.bet365.es/
- Pinnacle → https://www.pinnacle.com/en/basketball/nba
- William Hill → https://sports.williamhill.es/
- Betfair → https://www.betfair.com/exchange/plus/
- Codere → https://www.codere.es/deportes
- Bwin → https://sports.bwin.es/
- Marathon Bet → https://www.marathonbet.es/
- Unibet → https://www.unibet.es/

**¿Cómo llegas al mercado exacto?**
1. Click en el enlace
2. Busca el partido en la casa
3. Busca el jugador/mercado
4. Verifica que la cuota sea similar
5. Coloca la apuesta

---

## 📊 Interpretar los Datos

### **Expected Value (EV)**

```
EV = (Prob_Model × (Odds - 1)) - ((1 - Prob_Model) × 1)
```

**Ejemplo**:
```
Model Prob: 58.3%
Odds: 1.90
EV = (0.583 × 0.90) - (0.417 × 1)
EV = 0.525 - 0.417 = 0.108 = +10.8%
```

**Interpretación**:
- EV > 5% → Apuesta con valor
- EV > 8% → Muy buena apuesta
- EV < 3% → No apostar

---

### **Model Probability vs Implied Odds**

**Ejemplo de pick**:
```
LeBron James - Points OVER 25.5 @ 1.90
Model Prob: 58.3%
Implied Prob: 1/1.90 = 52.6%

Diferencia: 58.3% - 52.6% = 5.7% edge
```

**Esto significa**:
- El modelo cree que hay 58.3% de probabilidad de OVER
- Las odds implican 52.6%
- Tienes 5.7% de ventaja

---

### **Adjusted Stake %**

**Cómo se calcula**:
```
Adjusted Stake = Base Stake × Kelly Fraction
Adjusted Stake = min(Adjusted Stake, Max Stake %)
```

**Ejemplo**:
```
Base Kelly Stake: 8%
Kelly Fraction: 0.25
Max Stake: 5%

Adjusted = 8% × 0.25 = 2%  ✅ (menor que max)

Si Base fuera 25%:
Adjusted = 25% × 0.25 = 6.25%
Capped at Max Stake = 5%  ✅
```

---

## 🐛 Troubleshooting

### **"📭 No picks found matching your filters"**

**Causas posibles**:
1. No hay picks en la DB
   - **Solución**: `python scripts/run_predictions.py`

2. Filtros muy restrictivos
   - **Solución**: Bajar EV threshold (ej: de 8% a 3%)

3. No hay partidos hoy
   - **Solución**: Ampliar rango de fechas

---

### **"❌ Cannot connect to database"**

**Solución**:
```bash
python -c "from src.database import init_db; init_db()"
```

---

### **"📭 No odds data found"**

**Solución**:
```bash
# Colectar odds
python scripts/collect_data.py
```

---

### **"🟡 Odds API Not Configured"**

**Solución**:
1. Obtén API key: https://the-odds-api.com/
2. Edita `.env`:
   ```bash
   THE_ODDS_API_KEY=tu_key_aqui
   ```
3. Reinicia dashboard

---

### **Enlaces a bookmakers no funcionan**

**Causa**: URLs pueden cambiar

**Solución**:
1. Edita `config/books.yaml`
2. Actualiza URLs de bookmakers
3. Reinicia dashboard

---

## ⚡ Quick Reference

### **Comandos Esenciales**

```bash
# Iniciar dashboard
streamlit run app.py

# Colectar odds
python scripts/collect_data.py

# Generar predicciones
python scripts/run_predictions.py

# Actualizar resultados
python scripts/update_results.py

# Inicializar DB
python -c "from src.database import init_db; init_db()"

# Test datos reales
python test_datos_reales.py
```

---

### **Shortcuts en el Dashboard**

| Acción | Método |
|--------|--------|
| Cambiar riesgo | Ajustar sliders en sidebar |
| Filtrar deporte | Multiselect en sidebar |
| Refresh datos | Botón "🔄 Refresh Data" |
| Ver detalle pick | Click en fila expandible |
| Ir a bookmaker | Click en enlace 🔗 |
| Cambiar período histórico | Dropdown en tab Historical |

---

### **Valores Recomendados**

| Perfil | EV Min | Kelly | Max Stake | Odds Range |
|--------|--------|-------|-----------|------------|
| **Conservador** | 8% | 0.20 | 3% | 1.7-2.2 |
| **Moderado** | 5% | 0.25 | 5% | 1.7-2.5 |
| **Agresivo** | 3% | 0.30 | 7% | 1.5-3.0 |

---

## 🎯 Checklist Diario

```
[ ] Abrir dashboard: streamlit run app.py
[ ] Verificar status (🟢 DB + 🟢 API en header)
[ ] Ajustar controles de riesgo en sidebar
[ ] Seleccionar deportes de interés
[ ] Revisar tab "Today" para picks del día
[ ] Click en picks para ver análisis detallado
[ ] Verificar lesiones MANUALMENTE (ESPN)
[ ] Click en 🔗 para ir a bookmaker
[ ] Colocar apuestas manualmente
[ ] Por la noche: actualizar resultados
[ ] Revisar tab "Historical" para ver ROI
```

---

## 🚀 Mejoras Futuras

**Próximas funciones** (ver `QUE_FALTA_PARA_SER_PROFESIONAL.md`):
- ✅ Alertas Telegram automáticas
- ✅ Tracking de lesiones en tiempo real
- ✅ Gráficos de line movement
- ✅ Auto-refresh cada X minutos
- ✅ Filtros por bookmaker
- ✅ Comparación CLV (Closing Line Value)

---

## 📚 Recursos

- **Configurar API Key**: `COMO_OBTENER_API_KEY.md`
- **Datos Reales**: `CONFIGURAR_DATOS_REALES.md`
- **Guía Predicciones**: `docs/COMO_HACER_PREDICCIONES.md`
- **Fuentes de Datos**: `docs/FUENTES_DE_DATOS_Y_URLS.md`
- **Roadmap Profesional**: `QUE_FALTA_PARA_SER_PROFESIONAL.md`

---

**¡Disfruta del dashboard mejorado!** 🎉

Si tienes problemas, consulta la sección **Troubleshooting** o revisa los comandos en tab **Config**.
