#!/usr/bin/env python3
"""
Script para migrar handlers a usar get_service con context manager.
Versión corregida con manejo de indentación adecuado.
"""
import re
import os

def convert_handler(filepath):
    """Convierte un archivo handler para usar get_service con context manager."""
    with open(filepath, 'r') as f:
        content = f.read()

    filename = os.path.basename(filepath)

    # Extraer el nombre del servicio del archivo
    # Ej: category_admin_handlers.py -> PackageService
    service_map = {
        'category_admin_handlers.py': 'PackageService',
        'mission_admin_handlers.py': 'MissionService',
        'mission_user_handlers.py': 'MissionService',
        'package_handlers.py': 'PackageService',
        'promotion_admin_handlers.py': 'PromotionService',
        'promotion_user_handlers.py': 'PromotionService',
        'reward_admin_handlers.py': 'RewardService',
        'store_admin_handlers.py': 'StoreService',
        'story_admin_handlers.py': 'StoryService',
        'story_user_handlers.py': 'StoryService',
    }

    if filename not in service_map:
        print(f"  SKIP: {filename} no en mapa")
        return

    service_name = service_map[filename]
    service_var = service_name.replace('Service', '_service').lower()

    # Añadir import de get_service si no existe
    if 'from services import get_service' not in content:
        content = content.replace(
            'from services.package_service import PackageService',
            'from services import get_service\nfrom services.package_service import PackageService'
        )
        content = content.replace(
            'from services.mission_service import MissionService',
            'from services import get_service\nfrom services.mission_service import MissionService'
        )
        content = content.replace(
            'from services.promotion_service import PromotionService',
            'from services import get_service\nfrom services.promotion_service import PromotionService'
        )
        content = content.replace(
            'from services.reward_service import RewardService',
            'from services import get_service\nfrom services.reward_service import RewardService'
        )
        content = content.replace(
            'from services.store_service import StoreService',
            'from services import get_service\nfrom services.store_service import StoreService'
        )
        content = content.replace(
            'from services.story_service import StoryService',
            'from services import get_service\nfrom services.story_service import StoryService'
        )

    # Convertir cada bloque: service_var = Service() ... service.close()
    # al formato: with get_service(Service) as service_var: ...
    lines = content.split('\n')
    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Buscar patrón: {var} = {Service}()
        # Ej: package_service = PackageService()
        pattern = rf'^(\s*)({service_var})\s*=\s*{service_name}\(\)$'
        match = re.match(pattern, line)

        if match:
            indent = match.group(1)
            # Añadir la línea with
            new_lines.append(f'{indent}with get_service({service_name}) as {service_var}:')
            i += 1

            # Recolectar todas las líneas hasta .close()
            block_lines = []
            while i < len(lines):
                curr = lines[i]

                # Si encontramos .close(), lo omitimos (el context manager lo hace)
                if f'{service_var}.close()' in curr:
                    i += 1
                    continue

                # Si encontramos otra asignación de servicio o fin de función, detener
                if re.match(rf'^\s*{service_var}\s*=', curr) or (curr.strip().startswith('def ') and not curr.strip().startswith('def ')):
                    break

                # Si encontramos un nuevo handler/función, detener
                if re.match(r'^@router\.|^async def |^def ', curr):
                    break

                block_lines.append(curr)
                i += 1

            # Añadir las líneas del bloque con indentación adicional
            block_indent = indent + '    '
            for bl in block_lines:
                if bl.strip():
                    new_lines.append(block_indent + bl)
                else:
                    new_lines.append(bl)
        else:
            new_lines.append(line)
            i += 1

    content = '\n'.join(new_lines)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"  Convertido: {filename}")


def main():
    """Procesa todos los archivos de handlers."""
    print("Migrando handlers a get_service...")

    handlers_dir = "handlers"
    files_to_convert = [
        "category_admin_handlers.py",
        "mission_admin_handlers.py",
        "mission_user_handlers.py",
        "package_handlers.py",
        "promotion_admin_handlers.py",
        "promotion_user_handlers.py",
        "reward_admin_handlers.py",
        "store_admin_handlers.py",
        "story_admin_handlers.py",
        "story_user_handlers.py",
    ]

    for filename in files_to_convert:
        filepath = os.path.join(handlers_dir, filename)
        if os.path.exists(filepath):
            convert_handler(filepath)
        else:
            print(f"  NO ENCONTRADO: {filepath}")

    print("\nListo!")


if __name__ == "__main__":
    main()