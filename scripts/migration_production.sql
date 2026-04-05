-- ============================================
-- MIGRACIÓN DE CONFIGURACIÓN A PRODUCCIÓN
-- Lucien Bot - Sistema de Gamificación
-- ============================================

-- Ejecutar en orden:
-- 1. psql $DATABASE_URL -f scripts/migration_production.sql

-- ============================================
-- 1. EMOJIS DE REACCIÓN
-- ============================================
INSERT INTO reaction_emojis (emoji, name, besito_value, is_active, created_at)
VALUES
    ('🔥', 'Fuego', 2, true, NOW()),
    ('😈', 'Diablillo', 2, true, NOW()),
    ('💋', 'Beso', 2, true, NOW()),
    ('❤️', 'Corazón', 2, true, NOW())
ON CONFLICT (emoji) DO UPDATE SET
    besito_value = EXCLUDED.besito_value,
    is_active = true;

-- ============================================
-- 2. CONFIGURACIÓN REGALO DIARIO
-- ============================================
INSERT INTO daily_gift_config (besito_amount, is_active, updated_at)
VALUES (5, true, NOW())
ON CONFLICT (id) DO UPDATE SET
    besito_amount = EXCLUDED.besito_amount,
    is_active = true;

-- ============================================
-- 3. PAQUETES
-- ============================================
-- Nota: Guardar los IDs generados para los siguientes pasos
INSERT INTO packages (name, description, store_stock, reward_stock, is_active, created_at)
VALUES
    ('Pack Bienvenida - 5 Fotos', 'Pack de 5 fotos para onboarding (primera reacción)', -1, -1, true, NOW()),
    ('Pack 1 - 10 Fotos', 'Pack de 10 fotos', -1, -2, true, NOW()),
    ('Pack 2 - 20 Fotos', 'Pack de 20 fotos (requiere racha)', -1, -2, true, NOW()),
    ('Pack 3 - 30 Fotos VIP', 'Pack de 30 fotos exclusivo para VIP', -1, -2, true, NOW()),
    ('Pack Sorpresa', 'Entre 5 y 15 fotos aleatorias', -1, -2, true, NOW()),
    ('Pool Sorpresa', 'Pool de contenido para packs sorpresa', -1, -2, true, NOW())
ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 4. OBTENER IDS DE PAQUETES PARA REFERENCIAS
-- ============================================
-- Ejecutar esto y anotar los IDs:
-- SELECT id, name FROM packages WHERE name LIKE 'Pack%' ORDER BY id;

-- ============================================
-- 5. PRODUCTOS DE TIENDA
-- ============================================
-- NOTA: Reemplazar los ? con los IDs reales de los paquetes
-- Descomenta y ajusta según los IDs obtenidos:

-- INSERT INTO store_products (name, description, package_id, price, stock, is_active, created_at)
-- VALUES
--     ('Pack 1 - 10 Fotos', '10 fotos para disfrutar', ?, 80, -1, true, NOW()),
--     ('Pack 2 - 20 Fotos', '20 fotos (desbloquea con racha de 3 reacciones)', ?, 150, -1, true, NOW()),
--     ('Pack 3 - 30 Fotos VIP', '30 fotos exclusivo para miembros VIP', ?, 300, -1, true, NOW()),
--     ('Pack Sorpresa', 'Entre 5 y 15 fotos aleatorias', ?, 70, -1, true, NOW())
-- ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 6. RECOMPENSAS
-- ============================================
-- Primero las de tipo BESITOS (no requieren package_id)
INSERT INTO rewards (name, description, reward_type, besito_amount, is_active, created_at)
VALUES
    ('Besitos - Recompensa Básica', '5 besitos por reaccionar', 'besitos', 5, true, NOW()),
    ('Besitos - Recompensa Racha', '15 besitos por racha de 3 posts', 'besitos', 15, true, NOW())
ON CONFLICT (name) DO NOTHING;

-- Luego la de tipo PACKAGE (requiere package_id del Pack Bienvenida)
-- NOTA: Reemplazar ? con el ID del Pack Bienvenida
-- INSERT INTO rewards (name, description, reward_type, package_id, is_active, created_at)
-- VALUES ('Pack Bienvenida', 'Pack de 5 fotos para nuevos usuarios', 'package', ?, true, NOW())
-- ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 7. MISIONES
-- ============================================
-- NOTA: Reemplazar los ? con los IDs de las recompensas correspondientes
-- Primero obtener los IDs:
-- SELECT id, name FROM rewards WHERE name LIKE 'Besitos%';

-- INSERT INTO missions (name, description, mission_type, target_value, frequency, reward_id, is_active, created_at)
-- VALUES
--     ('Reacciona y Gana', 'Reacciona a la última publicación para ganar besitos', 'reaction_count', 1, 'recurring', ?, true, NOW()),
--     ('Racha de 3 Posts', 'Reacciona a 3 publicaciones consecutivas para obtener la recompensa de racha', 'reaction_count', 3, 'recurring', ?, true, NOW())
-- ON CONFLICT (name) DO NOTHING;

-- ============================================
-- 8. ARQUETIPOS
-- ============================================
INSERT INTO archetypes (archetype_type, name, description, unlock_description, welcome_message, created_at)
VALUES
    ('seductor', 'El Seductor', 'Busca el placer y la conquista. Disfruta del juego de la seducción y la atracción mutua.', 'Sumando puntos al elegir opciones que buscan placer y disfrute.', 'Bienvenido al círculo de los que buscan el placer sin reservas...', NOW()),
    ('observer', 'El Observador', 'Analiza y contempla. Valora los detalles y la estética cuidada.', 'Sumando puntos al elegir opciones que valoran la contemplación.', 'Tu mirada atenta no escapa nada. Bienvenido, Observador...', NOW()),
    ('devoto', 'El Devoto', 'Leal y dedicado. Busca la conexión genuina y la cercanía.', 'Sumando puntos al elegir opciones que priorizan la conexión.', 'Tu lealtad es tu mayor virtud. El círculo te recibe, Devoto...', NOW()),
    ('explorador', 'El Explorador', 'Curioso y aventurero. Busca la novedad y el descubrimiento constante.', 'Sumando puntos al elegir opciones que buscan nuevas experiencias.', 'Siempre hay algo nuevo por descubrir. Adelante, Explorador...', NOW()),
    ('misterioso', 'El Misterioso', 'Enigmático y reservado. Atraído por lo oculto y el significado profundo.', 'Sumando puntos al elegir opciones que buscan profundidad.', 'Los secretos te llaman. Bienvenido al lado misterioso...', NOW()),
    ('intrepido', 'El Intrépido', 'Audaz y sin miedo. Busca la emoción intensa y los límites.', 'Sumando puntos al elegir opciones audaces y sin filtros.', 'Sin miedo, sin límites. El círculo te espera, Intrépido...', NOW())
ON CONFLICT (archetype_type) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    unlock_description = EXCLUDED.unlock_description,
    welcome_message = EXCLUDED.welcome_message;

-- ============================================
-- VERIFICACIÓN
-- ============================================
-- Descomenta para verificar:
-- SELECT 'Emojis' as tabla, COUNT(*) as total FROM reaction_emojis WHERE is_active = true
-- UNION ALL
-- SELECT 'Paquetes', COUNT(*) FROM packages WHERE is_active = true
-- UNION ALL
-- SELECT 'Productos', COUNT(*) FROM store_products WHERE is_active = true
-- UNION ALL
-- SELECT 'Recompensas', COUNT(*) FROM rewards WHERE is_active = true
-- UNION ALL
-- SELECT 'Misiones', COUNT(*) FROM missions WHERE is_active = true
-- UNION ALL
-- SELECT 'Arquetipos', COUNT(*) FROM archetypes;
