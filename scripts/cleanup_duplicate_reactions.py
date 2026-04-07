"""
Limpia reacciones duplicadas antes de aplicar el constraint único.
Mantiene solo la primera reacción de cada usuario por broadcast.
"""
import sys
sys.path.insert(0, '/data/data/com.termux/files/home/repos/lucien_bot')

from models.database import SessionLocal
from sqlalchemy import text

def cleanup_duplicate_reactions():
    session = SessionLocal()
    try:
        # Encontrar duplicados
        duplicates = session.execute(text('''
            SELECT broadcast_id, user_id, COUNT(*) as count, MIN(id) as keep_id
            FROM broadcast_reactions
            GROUP BY broadcast_id, user_id
            HAVING COUNT(*) > 1
        ''')).fetchall()

        if not duplicates:
            print("No hay reacciones duplicadas")
            return

        total_removed = 0
        for dup in duplicates:
            broadcast_id, user_id, count, keep_id = dup
            # Eliminar todas las reacciones excepto la primera
            result = session.execute(text('''
                DELETE FROM broadcast_reactions
                WHERE broadcast_id = :broadcast_id
                AND user_id = :user_id
                AND id != :keep_id
            '''), {
                'broadcast_id': broadcast_id,
                'user_id': user_id,
                'keep_id': keep_id
            })
            removed = result.rowcount
            total_removed += removed
            print(f"Broadcast {broadcast_id}, User {user_id}: eliminadas {removed} duplicadas (mantenida id={keep_id})")

        session.commit()
        print(f"\nTotal de reacciones duplicadas eliminadas: {total_removed}")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_duplicate_reactions()
