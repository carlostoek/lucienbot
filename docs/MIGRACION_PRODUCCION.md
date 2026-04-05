# Guía de Migración a Producción - Lucien Bot

Este documento describe los pasos para migrar la configuración de gamificación desde el entorno local a Railway (producción).

---

## **Resumen de Datos a Migrar**

| Entidad | Cantidad | Descripción |
|---------|----------|-------------|
| Emojis de reacción | 4 | 🔥😈💋❤️ (2 besitos cada uno) |
| Configuración regalo diario | 1 | 5 besitos cada 24h |
| Paquetes | 6 | Vacíos, listos para archivos |
| Productos de tienda | 4 | Con precios en besitos |
| Recompensas | 3 | Besitos y paquetes |
| Misiones | 2 | Reacciona y Gana + Racha |
| Arquetipos | 6 | Descripciones configuradas |

---

## **Método 1: Ejecutar Script de Migración (Recomendado)**

### Paso 1: Acceder a Railway

```bash
# Instalar CLI de Railway (si no lo tienes)
npm install -g @railway/cli

# Login
railway login

# Enlazar proyecto
railway link
```

### Paso 2: Subir el script

```bash
# Asegúrate de tener el script en tu repo y hacer push
git add scripts/migrate_config_to_production.py
git commit -m "Add migration script for production config"
git push origin main
```

### Paso 3: Ejecutar en Railway

```bash
# Abrir shell de Railway
railway shell

# En el shell, ejecutar:
python scripts/migrate_config_to_production.py
```

O alternativamente:

```bash
# Ejecutar directamente
railway run python scripts/migrate_config_to_production.py
```

---

## **Método 2: Inserción SQL Manual**

Si prefieres ejecutar SQL directamente en la consola de PostgreSQL:

### 1. Conectar a la base de datos

```bash
# Obtener variables de entorno de Railway
railway variables

# Conectar con psql (usar la DATABASE_URL que te muestra Railway)
psql $DATABASE_URL
```

### 2. Ejecutar inserciones

```sql
-- 1. EMOJIS DE REACCIÓN
INSERT INTO reaction_emojis (emoji, name, besito_value, is_active) VALUES
    ('🔥', 'Fuego', 2, true),
    ('😈', 'Diablillo', 2, true),
    ('💋', 'Beso', 2, true),
    ('❤️', 'Corazón', 2, true);

-- 2. CONFIGURACIÓN REGALO DIARIO
INSERT INTO daily_gift_config (besito_amount, is_active) VALUES (5, true);

-- 3. PAQUETES (obtener IDs generados)
INSERT INTO packages (name, description, store_stock, reward_stock, is_active) VALUES
    ('Pack Bienvenida - 5 Fotos', 'Pack de 5 fotos para onboarding (primera reacción)', -1, -1, true),
    ('Pack 1 - 10 Fotos', 'Pack de 10 fotos', -1, -2, true),
    ('Pack 2 - 20 Fotos', 'Pack de 20 fotos (requiere racha)', -1, -2, true),
    ('Pack 3 - 30 Fotos VIP', 'Pack de 30 fotos exclusivo para VIP', -1, -2, true),
    ('Pack Sorpresa', 'Entre 5 y 15 fotos aleatorias', -1, -2, true),
    ('Pool Sorpresa', 'Pool de contenido para packs sorpresa', -1, -2, true);

-- Verificar IDs asignados
SELECT id, name FROM packages;

-- 4. PRODUCTOS DE TIENDA (ajustar package_id según IDs anteriores)
-- NOTA: Reemplazar ? con los IDs reales obtenidos
INSERT INTO store_products (name, description, package_id, price, stock, is_active) VALUES
    ('Pack 1 - 10 Fotos', '10 fotos para disfrutar', ?, 80, -1, true),
    ('Pack 2 - 20 Fotos', '20 fotos (desbloquea con racha de 3 reacciones)', ?, 150, -1, true),
    ('Pack 3 - 30 Fotos VIP', '30 fotos exclusivo para miembros VIP', ?, 300, -1, true),
    ('Pack Sorpresa', 'Entre 5 y 15 fotos aleatorias', ?, 70, -1, true);

-- 5. RECOMPENSAS
-- Primero obtener IDs de paquetes
-- Luego insertar recompensas

-- 6. ARQUETIPOS
INSERT INTO archetypes (archetype_type, name, description, unlock_description, welcome_message) VALUES
    ('seductor', 'El Seductor', 'Busca el placer y la conquista...', 'Sumando puntos al elegir opciones que buscan placer...', 'Bienvenido al círculo de los que buscan el placer...'),
    ('observer', 'El Observador', 'Analiza y contempla...', 'Sumando puntos al elegir opciones que valoran la contemplación...', 'Tu mirada atenta no escapa nada...'),
    ('devoto', 'El Devoto', 'Leal y dedicado...', 'Sumando puntos al elegir opciones que priorizan la conexión...', 'Tu lealtad es tu mayor virtud...'),
    ('explorador', 'El Explorador', 'Curioso y aventurero...', 'Sumando puntos al elegir opciones que buscan nuevas experiencias...', 'Siempre hay algo nuevo por descubrir...'),
    ('misterioso', 'El Misterioso', 'Enigmático y reservado...', 'Sumando puntos al elegir opciones que buscan profundidad...', 'Los secretos te llaman...'),
    ('intrepido', 'El Intrépido', 'Audaz y sin miedo...', 'Sumando puntos al elegir opciones audaces...', 'Sin miedo, sin límites...');
```

---

## **Verificación Post-Migración**

Después de ejecutar la migración, verifica que todo esté correcto:

```bash
# Conectar a Railway
railway connect postgres

# Ejecutar queries de verificación
```

### Queries de verificación:

```sql
-- Verificar emojis
SELECT emoji, name, besito_value FROM reaction_emojis WHERE is_active = true;

-- Verificar regalo diario
SELECT besito_amount, is_active FROM daily_gift_config;

-- Verificar paquetes
SELECT id, name, file_count, store_stock, reward_stock FROM packages WHERE is_active = true;

-- Verificar productos
SELECT name, price, stock FROM store_products WHERE is_active = true;

-- Verificar misiones
SELECT name, mission_type, target_value, frequency FROM missions WHERE is_active = true;

-- Verificar arquetipos
SELECT archetype_type, name FROM archetypes;
```

---

## **Paso Final: Subir Archivos a Paquetes**

Después de la migración de configuración, debes subir los archivos multimedia:

### 1. Iniciar el bot en producción

```bash
# Asegúrate de que el bot esté desplegado y funcionando
railway up
```

### 2. Acceder al menú de administración

1. Abre Telegram y busca tu bot
2. Ejecuta `/admin` (requiere ser admin)
3. Ve a: **Gestión de Paquetes** → **Actualizar paquete (agregar archivos)**

### 3. Subir archivos por paquete

| Paquete | Archivos necesarios |
|---------|---------------------|
| Pack Bienvenida | 5 fotos |
| Pack 1 | 10 fotos |
| Pack 2 | 20 fotos |
| Pack 3 | 30 fotos |
| Pack Sorpresa | 5-15 fotos aleatorias |
| Pool Sorpresa | 20+ fotos para random |

### Proceso:
1. Selecciona el paquete
2. Envía las fotos/videos uno por uno
3. Cuando termines, envía `/done`
4. Confirma la actualización

---

## **Rollback (En caso de problemas)**

Si necesitas revertir la migración:

```sql
-- Desactivar todo (no eliminar, solo desactivar)
UPDATE reaction_emojis SET is_active = false;
UPDATE packages SET is_active = false;
UPDATE store_products SET is_active = false;
UPDATE rewards SET is_active = false;
UPDATE missions SET is_active = false;
```

---

## **Troubleshooting**

### Error: "DATABASE_URL no está configurada"
```bash
export DATABASE_URL="postgresql://usuario:password@host:puerto/dbname"
```

### Error: "relation already exists"
El script maneja automáticamente duplicados. Si usas SQL manual, usa `ON CONFLICT` o verifica existencia primero.

### Error: "foreign key constraint"
Asegúrate de crear los paquetes ANTES que los productos/recompensas que los referencian.

---

## **Checklist Final**

- [ ] Script de migración ejecutado exitosamente
- [ ] Emojis de reacción configurados (4)
- [ ] Regalo diario configurado (5 besitos)
- [ ] Paquetes creados (6)
- [ ] Productos de tienda creados (4)
- [ ] Recompensas creadas (3)
- [ ] Misiones creadas (2)
- [ ] Arquetipos configurados (6)
- [ ] Archivos subidos a cada paquete
- [ ] Bot funcionando en producción
- [ ] Prueba de reacciones funcionando
- [ ] Prueba de regalo diario funcionando

---

**¿Problemas?** Revisa los logs del bot en Railway:
```bash
railway logs
```
