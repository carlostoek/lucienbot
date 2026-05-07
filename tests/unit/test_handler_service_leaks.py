"""
Tests de verificación post-fixes de leaks en handlers.

Estos tests verifican que los fixes fueron aplicados correctamente.
PASS = fix aplicado correctamente (código sano)
FAIL = fix no aplicado o incompleto (bug persiste)
"""
import pytest
import sys

sys.path.insert(0, '/home/ubuntu/repos/lucienbot')


class TestGameServiceLeaksFixed:
    """Verifica que GameService leaks fueron corregidos en game_user_handlers.py."""

    def test_no_direct_gameservice_instantiation_in_game_handlers(self):
        """
        CORRECTO: game_user_handlers.py NO debe tener instanciación directa de GameService().

        PASS = fix aplicado (no hay leaks)
        FAIL = fix no aplicado (todavía hay leaks)
        """
        import inspect
        from handlers import game_user_handlers

        source = inspect.getsource(game_user_handlers)
        lines = source.split('\n')
        direct_gameservice_lines = []

        for i, line in enumerate(lines):
            if '= GameService()' in line and 'with get_service' not in line:
                direct_gameservice_lines.append((i + 1, line.strip()))

        assert len(direct_gameservice_lines) == 0, (
            f"FIX INCOMPLETO: Se encontraron {len(direct_gameservice_lines)} instanciaciones "
            f"directas de GameService() sin context manager:\n" +
            '\n'.join([f"  Línea {ln}: {code}" for ln, code in direct_gameservice_lines])
        )

    def test_streak_handlers_use_class_templates_not_instance(self):
        """
        CORRECTO: Los handlers streak_* deben usar random.choice(GameService.TEMPLATES)
        en lugar de crear una instancia de GameService solo para _select_template().

        _select_template() es un método de clase que no necesita instancia.
        """
        import inspect
        from handlers import game_user_handlers

        source = inspect.getsource(game_user_handlers)

        # Buscar que se usa random.choice con GameService.STREAK_TEMPLATES
        assert 'random.choice(GameService.STREAK_TEMPLATES' in source, (
            "FIX INCOMPLETO: Los handlers de streak deben usar "
            "random.choice(GameService.STREAK_TEMPLATES[...]) en lugar de "
            "crear una instancia de GameService"
        )


class TestVIPServiceLeaksFixed:
    """Verifica que VIPService leaks fueron corregidos en story_user_handlers.py."""

    def test_vip_service_properly_closed_in_show_node(self):
        """
        CORRECTO: show_node() debe usar try/finally para cerrar VIPService.

        PASS = fix aplicado (VIPService cerrado correctamente)
        FAIL = fix no aplicado (VIPService no se cierra)
        """
        import inspect
        from handlers import story_user_handlers

        source = inspect.getsource(story_user_handlers.show_node)

        # Debe tener try/finally con vip_service.close()
        assert 'try:' in source, "show_node debe usar try/finally"
        assert 'vip_service.close()' in source, (
            "FIX INCOMPLETO: show_node debe llamar vip_service.close() en el bloque finally"
        )

    def test_vip_service_properly_closed_in_make_choice(self):
        """
        CORRECTO: make_choice() debe usar try/finally para cerrar VIPService.

        PASS = fix aplicado (VIPService cerrado correctamente)
        FAIL = fix no aplicado (VIPService no se cierra)
        """
        import inspect
        from handlers import story_user_handlers

        source = inspect.getsource(story_user_handlers.make_choice)

        # Debe tener try/finally con vip_service.close()
        assert 'try:' in source, "make_choice debe usar try/finally"
        assert 'vip_service.close()' in source, (
            "FIX INCOMPLETO: make_choice debe llamar vip_service.close() en el bloque finally"
        )

    def test_all_vip_service_instantiations_have_close(self):
        """
        CORRECTO: Todas las instancias de VIPService() en story_user_handlers.py
        deben estar protegidas con try/finally o context manager.

        PASS = todos los VIPService se cierran correctamente
        FAIL = hay VIPService sin close()
        """
        import inspect
        from handlers import story_user_handlers

        source = inspect.getsource(story_user_handlers)
        lines = source.split('\n')

        vip_service_locations = []
        for i, line in enumerate(lines):
            if 'VIPService()' in line:
                vip_service_locations.append((i + 1, line.strip()))

        # Verificar que cada función que usa VIPService tiene close()
        # Para cada VIPService(), buscar en qué función está y verificar que
        # esa función contiene vip_service.close()
        tested_functions = set()

        for line_num, line in vip_service_locations:
            # Determinar en qué función estamos
            # Buscar hacia atrás el def más cercano
            for j in range(line_num - 1, max(0, line_num - 100), -1):
                if lines[j].strip().startswith('async def ') or lines[j].strip().startswith('def '):
                    func_name = lines[j].strip().split('(')[0].replace('async def ', '').replace('def ', '')
                    func_name = func_name.strip()

                    # Si ya probamos esta función, no repetir
                    if func_name in tested_functions:
                        break

                    # Obtener el código de la función completa
                    func_source = inspect.getsource(getattr(story_user_handlers, func_name))

                    # Verificar que la función tiene close() para vip_service
                    has_close = 'vip_service.close()' in func_source

                    assert has_close, (
                        f"FIX INCOMPLETO: La función '{func_name}' crea VIPService() "
                        f"pero no tiene vip_service.close() en su cuerpo.\n"
                        f"  VIPService() encontrado en línea aproximada: {line_num}"
                    )

                    tested_functions.add(func_name)
                    break
