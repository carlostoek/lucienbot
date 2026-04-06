# Contexto: Mejorar Tienda (Fase 12)

## Visión General

Optimización completa de la tienda y el flujo de compra, integrando vistas detalladas de productos, catálogo general y un sistema de condicionalidad recíproca entre tienda, gamificación y narrativa.

## Requisitos Funcionales

### 1. Vistas de Producto Detalladas
- Catálogo general con todos los productos visibles para todos los usuarios
- Vista detallada por producto con especificación clara de condiciones de acceso:
  - Condición VIP requerida
  - Nivel narrativo específico requerido
- Previsualización para usuarios sin acceso completo

### 2. Flujo de Compra Optimizado
- Si usuario intenta comprar sin cumplir requisitos → invitación a satisfacer la condición
- Productos bloqueados muestran preview + CTA para suscribirse/obtener acceso
- Transición suave entre descubrimiento de producto y satisfacción de requisitos

### 3. Sistema de Condicionalidad en Cascada

#### Integración con Gamificación
- Reutilizar sistema de condiciones ya establecido en módulos de gamificación
- Revisar interacción tienda-gamificación-narrativa para coherencia

#### Condicionalidad Recíproca
```
Tienda → Narrativa: Productos desbloquean niveles narrativos
Narrativa → Tienda: Niveles narrativos desbloquean productos
Gamificación ↔ Todo: Besitos como moneda universal
```

### 4. Recompensas Interconectadas

Los niveles narrativos deben otorgar:
- Besitos (moneda de gamificación)
- Niveles de suscripción en canales
- Desbloqueo de niveles narrativos adicionales
- Productos de la tienda

### 5. Ecosistema Integrado

Todo el sistema opera bajo modelo de **condicionalidad recíproca**:
- Cada componente puede ser requisito o recompensa de otro
- Flujo unificado de integración entre dominios
- Experiencia coherente para el usuario final

## Dependencias a Revisar

- Sistema de condiciones existente en gamificación
- Sistema de niveles narrativos
- Sistema de suscripciones VIP
- Flujo de canje de tokens

## Notas de Implementación

- Todos los productos deben ser visibles (no ocultar productos VIP a usuarios free)
- La diferenciación es en el *acceso*, no en la *visibilidad*
- Previews estratégicos como hook de conversión
- Mantener coherencia con voz de Lucien en mensajes de bloqueo/invitación
