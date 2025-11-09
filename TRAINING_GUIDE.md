# 📚 Guía de Entrenamiento y Calibración de Modelos

## 🎯 Resumen: ¿Necesito Entrenar Modelos?

### Modelos Estadísticos (Por defecto) - **NO requieren entrenamiento ML**

Los modelos Poisson y Monte Carlo solo necesitan:
- ✅ Datos históricos para calcular promedios
- ✅ Calibración de factores multiplicadores
- ❌ **NO** necesitan entrenamiento como ML tradicional

### Modelos ML (Opcional) - **SÍ requieren entrenamiento**

Los modelos XGBoost/LightGBM (opcional) sí requieren:
- ✅ Entrenamiento con datos históricos
- ✅ Train/validation/test splits
- ✅ Optimización de hiperparámetros

---

## 📊 Flujo Completo: Datos → Modelos → Predicciones

```
1. DESCARGAR DATOS HISTÓRICOS
   └─> python scripts/populate_historical_data.py

2. CALIBRAR MODELOS ESTADÍSTICOS
   └─> python scripts/calibrate_models.py

3. (OPCIONAL) ENTRENAR MODELOS ML
   └─> python scripts/train_ml_models.py

4. GENERAR PREDICCIONES
   └─> python scripts/run_predictions.py

5. VISUALIZAR EN DASHBOARD
   └─> streamlit run app.py
```

---

## 1️⃣ Descargar Datos Históricos

### NBA (Más fácil - API oficial)

```bash
# Descargar últimas 2 temporadas de top 30 jugadores
python scripts/download_nba_history.py \
    --seasons 2023-24 2024-25 \
    --players 30

# Con importación automática a base de datos
python scripts/download_nba_history.py \
    --seasons 2023-24 2024-25 \
    --players 30 \
    --import-db
```

**Fuente**: NBA API oficial (gratis, ~60 req/min)

### Todos los deportes a la vez

```bash
# Quick mode: últimos 10 partidos por jugador/equipo
python scripts/populate_historical_data.py --quick

# Full mode: temporadas completas
python scripts/populate_historical_data.py \
    --sports nba laliga tennis acb \
    --seasons 2022-23 2023-24 2024-25
```

### Verificar datos descargados

```bash
# Ver estructura de archivos
ls -R data/raw/

# Ver registros en base de datos
sqlite3 data/results/sports_bot.db "SELECT COUNT(*) FROM player_stats;"
```

---

## 2️⃣ Calibrar Modelos Estadísticos (Poisson/Monte Carlo)

### ¿Qué hace la calibración?

**Ajusta factores multiplicadores:**
- Home/Away factor (ej: 1.05 para local, 0.95 para visitante)
- Opponent defense factor
- Pace/tempo factor
- Minutes correlation

**Valida precisión:**
- Brier Score (qué tan precisas son las probabilidades)
- Calibration Error (si P(over)=60%, ¿realmente pasa 60% de las veces?)

### Ejecutar calibración

```bash
python scripts/calibrate_models.py
```

**Output:**
```
CALIBRATED FACTORS:
  home_away_home: 1.052
  home_away_away: 0.948
  opponent_defense: 0.985

VALIDATION METRICS:
  Brier Score: 0.2134 (lower is better)
  Log Loss: 0.6521
  Calibration Error: 0.0234
```

**Factores guardados en**: `config/calibrated_factors.yaml`

### Usar factores calibrados

Editar `config/config.yaml` y añadir:

```yaml
models:
  calibrated_factors:
    home_factor: 1.052
    away_factor: 0.948
    opponent_defense: 0.985
```

---

## 3️⃣ (Opcional) Entrenar Modelos ML

### ¿Cuándo usar modelos ML?

**USA modelos ML si:**
- ✅ Tienes >2000 partidos de datos históricos
- ✅ Quieres capturar interacciones complejas entre features
- ✅ Buscas mejorar 1-2% de precisión vs Poisson

**NO uses modelos ML si:**
- ❌ Tienes pocos datos (<500 partidos)
- ❌ Prefieres simplicidad e interpretabilidad
- ❌ Los modelos Poisson ya tienen buen rendimiento

### Entrenar XGBoost/LightGBM

```bash
# Requiere instalar dependencias ML
pip install xgboost lightgbm scikit-learn

# Entrenar modelos
python scripts/train_ml_models.py
```

**Output:**
```
XGBOOST MODEL:
  MAE: 4.32 points
  RMSE: 6.18 points
  R²: 0.742

LIGHTGBM MODEL:
  MAE: 4.28 points
  RMSE: 6.15 points
  R²: 0.748

FEATURE IMPORTANCE:
  pts_mean_5: 0.324
  min_mean_5: 0.187
  opp_def_rating: 0.145
  ...
```

**Modelos guardados en**: `data/models/`

### Usar modelo ML en predicciones

```python
import pickle
from pathlib import Path

# Cargar modelo
model_path = Path('data/models/xgboost_points.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)

# Predecir
prediction = model.predict(features)
```

---

## 4️⃣ Validar Precisión de Modelos

### Métricas clave

**Para valores continuos (puntos, rebounds):**
- **MAE** (Mean Absolute Error): Error promedio en puntos
  - Bueno: <5 puntos para NBA
  - Excelente: <3 puntos
- **R²** (R-squared): % de varianza explicada
  - Bueno: >0.6
  - Excelente: >0.75

**Para probabilidades (Over/Under):**
- **Brier Score**: Qué tan precisas son las probabilidades
  - Perfecto: 0
  - Bueno: <0.25
  - Malo: >0.30
- **Calibration Error**: Si predices 60%, ¿pasa 60%?
  - Bueno: <0.05
  - Excelente: <0.02

### Verificar calibración

```python
from src.models.calibration import ModelValidator

# Probabilidades predichas vs resultados reales
validator = ModelValidator()
calibration_data = validator.probability_calibration_plot_data(
    predicted_probs=[0.45, 0.52, 0.68, ...],
    actual_outcomes=[0, 1, 1, ...]
)

print(calibration_data)
#    predicted_prob  actual_freq  count
# 0       0.45          0.43       120
# 1       0.52          0.54       95
# 2       0.68          0.65       87
```

---

## 5️⃣ Comparación: Poisson vs ML

### Poisson (Estadístico)

**Pros:**
- ✅ Rápido y simple
- ✅ Interpretable (sabes por qué predice X)
- ✅ Funciona bien con pocos datos
- ✅ Incorpora conocimiento del dominio (distribución de eventos)

**Contras:**
- ❌ Asume independencia de eventos
- ❌ No captura interacciones complejas

**Cuándo usar:** Default, siempre funciona bien

### XGBoost/LightGBM (ML)

**Pros:**
- ✅ Captura interacciones complejas
- ✅ 1-3% mejor precisión (típico)
- ✅ Maneja no-linearidades

**Contras:**
- ❌ Requiere más datos (>1000 muestras)
- ❌ Menos interpretable
- ❌ Puede sobreajustar con pocos datos
- ❌ Más lento

**Cuándo usar:** Cuando tienes muchos datos y buscas máxima precisión

### Comparación típica

```
Métrica          Poisson    XGBoost    Mejora
────────────────────────────────────────────────
MAE (puntos)     5.2        4.8        -7.7%
R²               0.68       0.72       +5.9%
Brier Score      0.243      0.229      -5.8%
Velocidad        ⚡⚡⚡      ⚡⚡        33% más lento
Interpretable    ✅         ❌         -
```

---

## 6️⃣ Re-entrenamiento/Re-calibración

### Frecuencia recomendada

**Calibración de factores:**
- Mensual durante temporada activa
- Trimestral fuera de temporada

**Modelos ML:**
- Mensual con datos nuevos
- Después de cambios de reglas/formato

### Script automatizado

```bash
# Actualizar todo (datos + calibración + ML)
./scripts/update_all.sh

# Solo re-calibrar (rápido)
python scripts/calibrate_models.py

# Solo re-entrenar ML
python scripts/train_ml_models.py
```

---

## 7️⃣ Troubleshooting

### "Brier Score muy alto (>0.30)"

**Causas:**
- Factores mal calibrados
- Poco datos históricos
- Cambios en el juego (lesiones, trades)

**Solución:**
```bash
# Re-calibrar con más datos
python scripts/populate_historical_data.py --seasons 2021-22 2022-23 2023-24
python scripts/calibrate_models.py
```

### "MAE muy alto (>7 puntos en NBA)"

**Causas:**
- Features no relevantes
- Falta considerar contexto (minutos, oponente)
- Datos de baja calidad

**Solución:**
- Añadir más features (ver `src/features/feature_engineering.py`)
- Filtrar outliers
- Validar calidad de datos

### "Modelo sobreajusta (train R²=0.9, test R²=0.5)"

**Causas:**
- Modelo ML muy complejo
- Pocos datos

**Solución:**
```python
# Reducir complejidad de modelo ML
model = xgb.XGBRegressor(
    max_depth=3,  # en vez de 6
    min_child_weight=5  # más regularización
)
```

---

## 8️⃣ Resumen Quick Start

### Mínimo viable (solo Poisson)

```bash
# 1. Descargar últimos 10 partidos
python scripts/populate_historical_data.py --quick

# 2. Calibrar
python scripts/calibrate_models.py

# 3. Predecir
python scripts/run_predictions.py

# 4. Ver dashboard
streamlit run app.py
```

**Tiempo**: ~10 minutos
**Datos requeridos**: ~150 partidos

### Full stack (Poisson + ML)

```bash
# 1. Descargar 2 temporadas completas
python scripts/populate_historical_data.py \
    --seasons 2023-24 2024-25 \
    --sports nba laliga

# 2. Calibrar Poisson
python scripts/calibrate_models.py

# 3. Entrenar ML
pip install xgboost lightgbm
python scripts/train_ml_models.py

# 4. Dashboard
streamlit run app.py
```

**Tiempo**: ~2 horas
**Datos requeridos**: ~2000+ partidos

---

## ✅ Checklist de Implementación

- [ ] Datos históricos descargados (>100 partidos)
- [ ] Base de datos inicializada
- [ ] Factores Poisson calibrados (Brier <0.25)
- [ ] (Opcional) Modelos ML entrenados
- [ ] Validación en hold-out set (R² >0.6)
- [ ] Dashboard funcionando
- [ ] Primeras predicciones generadas

---

## 📚 Recursos Adicionales

- [Documentación de fuentes de datos](docs/DATA_SOURCES.md)
- [Código de modelos](src/models/)
- [Ejemplo de calibración](scripts/calibrate_models.py)
