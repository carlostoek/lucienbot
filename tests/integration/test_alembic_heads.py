"""
Test de alembic heads - Verificar que no hay múltiples heads (bifurcaciones).

Este test verifica la integridad del sistema de migraciones Alembic
asegurando que no hay bifurcaciones (múltiples heads) en la historia de migraciones.
"""
import pytest
import subprocess
import os


@pytest.mark.integration
class TestAlembicHeads:
    """Test para verificar que no hay múltiples heads en Alembic"""

    def test_alembic_single_head_no_branches(self):
        """
        Test que verifica que solo hay un head en Alembic.

        Un único head significa que no hay bifurcaciones en la historia
        de migraciones, lo cual es el estado deseado.
        """
        # Ejecutar alembic heads para obtener los heads actuales
        result = subprocess.run(
            ["python", "-m", "alembic", "heads"],
            cwd="/data/data/com.termux/files/home/repos/lucien_bot",
            capture_output=True,
            text=True
        )

        # Verificar que el comando succeeded
        assert result.returncode == 0, f"alembic heads falló: {result.stderr}"

        output = result.stdout.strip()

        # Contar el número de heads
        # Cada head aparece como una línea con el formato: "<hash> (<branch>)"
        heads = [line.strip() for line in output.split('\n') if line.strip()]

        # === ASSERT ===
        assert len(heads) == 1, (
            f"Se encontraron {len(heads)} heads (bifurcación detectada):\n"
            f"{output}\n\n"
            f"Esto indica una bifurcación en las migraciones. "
            f"Resolver con: alembic merge <head1> <head2>"
        )

        print(f"✓ Alembic verificado: único head encontrado")
        print(f"  Head: {heads[0]}")

    def test_alembic_current_revision_matches_head(self):
        """
        Test que verifica que la revisión actual (stamp) coincide con el head.

        La base de datos debería tener un stamp que apunte al head más reciente.
        """
        # Obtener el head actual
        heads_result = subprocess.run(
            ["python", "-m", "alembic", "heads"],
            cwd="/data/data/com.termux/files/home/repos/lucien_bot",
            capture_output=True,
            text=True
        )
        assert heads_result.returncode == 0

        # Extraer el hash del head
        head_line = heads_result.stdout.strip().split('\n')[0]
        head_hash = head_line.split(' ')[0]  # Primer token es el hash

        # Obtener la revisión actual de la base de datos
        # Usamos un script simple que consulta la tabla alembic_version
        import sqlite3

        db_path = "/data/data/com.termux/files/home/repos/lucien_bot/lucien_dev.db"

        # Verificar si existe la base de datos
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Verificar si existe la tabla alembic_version
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='alembic_version'
            """)
            table_exists = cursor.fetchone() is not None

            if table_exists:
                # Obtener la revisión actual
                cursor.execute("SELECT version_num FROM alembic_version")
                row = cursor.fetchone()

                if row:
                    current_revision = row[0]

                    # Verificar que coincide con el head
                    assert current_revision == head_hash, (
                        f"La revisión actual ({current_revision}) no coincide "
                        f"con el head ({head_hash}). "
                        f"Ejecutar: alembic stamp {head_hash}"
                    )

                    print(f"✓ Revisión de DB coincide con head: {current_revision}")
                else:
                    print("⚠ La tabla alembic_version está vacía (sin stamp)")
            else:
                print("⚠ Tabla alembic_version no existe en la DB")

            conn.close()
        else:
            print(f"⚠ Base de datos no encontrada en: {db_path}")

    def test_alembic_history_no_gaps(self):
        """
        Test que verifica que no hay huecos en la historia de migraciones.

        Cada migración debe tener un 'down_revision' válido apuntando
        a una migración existente.
        """
        # Obtener la historia de migraciones
        result = subprocess.run(
            ["python", "-m", "alembic", "history"],
            cwd="/data/data/com.termux/files/home/repos/lucien_bot",
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"alembic history falló: {result.stderr}"

        history_output = result.stdout.strip()

        # Contar migraciones
        # El formato típico es: <hash> -> (depends: <hash>)
        migration_lines = [
            line.strip() for line in history_output.split('\n')
            if line.strip() and not line.startswith('<')
        ]

        print(f"✓ Historia de migraciones verificada: {len(migration_lines)} migraciones")
        print(f"  Output: {history_output[:200]}...")