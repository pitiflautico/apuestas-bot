# 🔑 Cómo Obtener THE_ODDS_API_KEY (Gratis)

## Paso 1: Registro en The Odds API

1. Ve a: **https://the-odds-api.com/**
2. Click en "**Get API Key**" (botón naranja)
3. Rellena el formulario:
   - Email
   - Nombre
   - Uso: "Personal / Research"
4. Click en "**Sign Up**"

## Paso 2: Obtener tu Key

1. Recibirás un email de confirmación
2. Click en el enlace del email
3. Inicia sesión en: https://the-odds-api.com/account/
4. Copia tu **API Key** (ej: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)

## Paso 3: Configurar en el Bot

1. Abre el archivo `.env` en la raíz del proyecto
2. Reemplaza las X por tu key:
   ```bash
   THE_ODDS_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
   ```
3. Guarda el archivo

## ✅ Verificar

Ejecuta:
```bash
python test_datos_reales.py
```

Deberías ver:
```
✅ THE_ODDS_API_KEY configurada: a1b2c3d4...
✅ The Odds API funciona - X partidos obtenidos
   → CUOTAS REALES ✅
```

## 📊 Plan Gratis vs Pago

### Plan Gratis (Suficiente para empezar):
- ✅ **500 requests/mes**
- ✅ Todos los deportes
- ✅ Todos los mercados (h2h, totals, spreads, props)
- ✅ Datos en vivo
- ⏱️ Rate limit: 10 requests/minuto

### Cálculo de Consumo:
```
1 request = 1 deporte × 1 mercado

Ejemplo uso diario:
- NBA (h2h, totals, player_points): 3 requests
- EuroLeague (h2h, totals): 2 requests
- La Liga (h2h): 1 request
= 6 requests/día × 30 días = 180 requests/mes

→ Plan gratis es SUFICIENTE para uso normal
```

### Plan Pago ($59/mes):
- **5,000 requests/mes**
- Mejor para bots automáticos que consultan cada hora

## 💡 Tips para Ahorrar Requests

1. **Cachear resultados**: No consultar la misma cuota varias veces
   ```python
   # Guardar odds en DB y reutilizar durante 15 min
   ```

2. **Consultar solo deportes activos**: No consultar NBA en verano
   ```python
   sports = ['euroleague'] if month in [10,11,12,1,2,3,4] else ['laliga']
   ```

3. **Agrupar markets**: Obtener varios mercados en 1 request
   ```python
   markets=['h2h', 'totals', 'spreads']  # 1 request en vez de 3
   ```

## 🔧 Troubleshooting

### "Invalid API Key"
- Verifica que copiaste la key completa (sin espacios)
- Comprueba que confirmaste el email de registro

### "Rate limit exceeded"
- Estás haciendo más de 10 requests/minuto
- Añade `time.sleep(6)` entre requests

### "Quota exceeded"
- Has superado 500 requests este mes
- Espera al próximo mes o upgrade a plan pago
- Consulta uso en: https://the-odds-api.com/account/

## 📞 Soporte

- Documentación: https://the-odds-api.com/liveapi/guides/v4/
- Email: support@the-odds-api.com
- GitHub: https://github.com/the-odds-api

---

**¡Listo!** Con tu API key configurada, el bot usará **datos 100% reales** 🚀
