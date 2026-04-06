# WebApp - Juego de Dados

Documentación para configurar y deployar la WebApp del juego de dados.

## Archivos

- `webapp/dice.html` - Página principal del juego
- `webapp/css/dice.css` - Estilos
- `webapp/js/dice.js` - Lógica del juego

## Desarrollo Local

### 1. Iniciar servidor de archivos estáticos

```bash
python -m http.server 8080 --directory webapp/
```

Acceder a: http://localhost:8080/dice.html

### 2. Configurar variables de entorno

Editar `.env`:
```env
WEBAPP_URL=http://localhost:8080/webapp/dice.html
WEBAPP_DEV_URL=http://localhost:8080/webapp/dice.html
```

### 3. Iniciar el bot

```bash
python bot.py
```

### 4. Testing con ngrok (para BotFather)

```bash
# Terminal 1: Servir archivos estáticos
python -m http.server 8080 --directory webapp/

# Terminal 2: Exponer con ngrok
ngrok http 8080

# Usar la URL de ngrok (ej: https://abc123.ngrok.io/webapp/dice.html)
# para configurar temporalmente en BotFather
```

## Producción (Railway)

### Opción 1: Railway + Archivos Estáticos (Recomendado)

Railway puede servir archivos estáticos de varias formas:

#### A. Usar buildpack de nginx (recomendado)

1. Agregar archivo `nginx.conf`:
```nginx
server {
    listen 8080;
    server_name localhost;
    
    location /webapp/ {
        alias /app/webapp/;
        try_files $uri $uri/ =404;
    }
    
    location / {
        proxy_pass http://localhost:8000;
    }
}
```

2. Actualizar `railway.toml`:
```toml
[build]
builder = "nixpacks"
NIXPACKS_PYTHON_VERSION = "3.11"

[deploy]
startCommand = "nginx -g 'daemon off;' & python bot.py"
```

#### B. Servir desde el bot con FastAPI (alternativo)

1. Agregar dependencia en `requirements.txt`:
```
fastapi
uvicorn
python-multipart
```

2. Crear archivo `webapp_server.py`:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()
app.mount("/webapp", StaticFiles(directory="webapp"), name="webapp")

@app.get("/webapp/dice.html")
async def dice():
    return FileResponse("webapp/dice.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

3. Actualizar `railway.toml`:
```toml
[deploy]
startCommand = "alembic upgrade head && uvicorn webapp_server:app --host 0.0.0.0 --port $PORT & python bot.py"
```

### Opción 2: Hosting Externo

Alternativamente, puedes hosting la WebApp en:

- **Cloudflare Pages**: Gratis, global CDN
- **GitHub Pages**: Gratis, ideal para repositorios públicos
- **Vercel**: Gratis, muy rápido

1. Subir carpeta `webapp/` al hosting externo
2. Obtener URL de producción
3. Configurar en Railway: `WEBAPP_URL=https://tu-dominio.com/dice.html`

## Configurar en BotFather

### Pasos

1. Abre @BotFather
2. Selecciona tu bot
3. Envía `/setmenubutton` o ve a Bot Settings → Menu Button → Configure
4. Establece el texto del botón: `🎲 Lanzar dados`
5. Establece la URL de WebApp:
   - Desarrollo: `http://localhost:8080/webapp/dice.html` (solo funciona en机等)
   - Producción: Tu URL de producción

### Para Testing

1. Inicia ngrok: `ngrok http 8080`
2. Usa la URL de ngrok en BotFather temporalmente
3. Prueba en Telegram
4. Cuando funcione, configura la URL de producción

## Verificación

### Checklist

- [ ] Servidor local funciona (python -m http.server)
- [ ] Bot responde con botón de WebApp
- [ ] WebApp abre en Telegram
- [ ] Dados muestran resultado
- [ ] Resultado se envía al bot
- [ ] Besitos se acreditan correctamente

### Testing Manual

1. Iniciar servidor: `python -m http.server 8080 --directory webapp/`
2. Iniciar bot: `python bot.py`
3. Abrir Telegram y buscar el bot
4. Navegar al menú de gamificación
5. Hacer clic en "🎲 Lanzar dados"
6. Jugar y verificar que los besitos se acreditan

## Solución de Problemas

### La WebApp no carga
- Verificar que la URL es accesible públicamente
- Verificar que el archivo existe en el servidor

### Los datos no llegan al bot
- Verificar que `WEBAPP_URL` está configurado correctamente en `.env`
- Revisar logs del bot para errores

### Error "Invalid data"
- Verificar que el JSON enviado desde el frontend tiene el formato correcto
- Revisar `handlers/gamification_user_handlers.py` línea ~474