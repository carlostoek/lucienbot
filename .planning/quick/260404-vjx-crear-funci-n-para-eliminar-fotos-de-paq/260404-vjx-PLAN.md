# Quick Task Plan: 260404-vjx

**Task:** Crear función para eliminar fotos de paquetes: mostrar fotos existentes con botón de eliminar en cada una

**Files:**
- `handlers/package_handlers.py` (modificar)
- `services/package_service.py` (existente, tiene `remove_file_from_package`)

## Task 1: Agregar estado FSM y menú de gestión de archivos

**File:** `handlers/package_handlers.py`

**Action:**
1. Agregar nuevo estado `DeleteFileStates` para el FSM
2. Agregar botón "🗑️ Eliminar archivos" en el menú de detalle de paquete (`package_detail`)
3. Crear handler `delete_package_files_start` para iniciar el flujo de eliminación

**Verify:**
- El botón aparece en el detalle del paquete
- Al hacer clic inicia el flujo de eliminación

## Task 2: Crear handler para mostrar archivos con botón eliminar

**File:** `handlers/package_handlers.py`

**Action:**
1. Crear handler `show_files_for_deletion` que:
   - Obtiene los archivos del paquete usando `package_service.get_package_files()`
   - Envía cada archivo como preview con un botón "🗑️ Eliminar" con callback `delfile_{file_id}`
   - Agrega botón "✅ Terminar" para volver al detalle del paquete
2. Crear handler `confirm_delete_file` que muestra confirmación
3. Crear handler `execute_delete_file` que elimina el archivo usando `package_service.remove_file_from_package()`

**Verify:**
- Cada archivo se muestra con su preview
- Cada archivo tiene botón para eliminar
- La eliminación funciona correctamente
- Después de eliminar, vuelve a mostrar los archivos restantes

## Task 3: Agregar botón al menú principal de paquetes

**File:** `handlers/package_handlers.py`

**Action:**
Agregar botón "🗑️ Eliminar archivos de paquete" en el menú principal `manage_packages_menu`

**Verify:**
- El botón aparece en el menú de gestión de paquetes
- Al hacer clic inicia el flujo de selección de paquete para eliminar archivos
