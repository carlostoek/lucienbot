"""
Tests unitarios para StoryService (atomicity fix para advance_to_node).
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, '/data/data/com.termux/files/home/repos/lucien_bot')

from services.story_service import StoryService
from models.models import (
    StoryNode, StoryChoice, UserStoryProgress, ArchetypeType,
    NodeType, TransactionSource
)


@pytest.mark.unit
class TestStoryServiceAtomicity:
    """Tests para verificar atomicidad de advance_to_node (Finding #2)."""

    def test_advance_to_node_calls_debit_besitos_with_commit_false(self, db_session, sample_user):
        """Test que advance_to_node pasa commit=False a debit_besitos."""
        # Setup: crear nodo con costo en besitos
        node = StoryNode(
            title="Test Node",
            content="Test content",
            node_type=NodeType.NARRATIVE,
            cost_besitos=10,
            chapter=1,
            is_active=True,
        )
        db_session.add(node)
        db_session.commit()

        # Setup: usuario con saldo suficiente y progreso inicial
        from models.models import BesitoBalance
        balance = BesitoBalance(
            user_id=sample_user.id,
            balance=100,
            total_earned=100,
            total_spent=0
        )
        db_session.add(balance)
        db_session.commit()

        service = StoryService(db_session)

        # Mock debit_besitos para verificar que se llama con commit=False
        original_debit = service.besito_service.debit_besitos
        debit_call_args = {}

        def mock_debit(user_id, amount, source, description=None, reference_id=None, commit=True):
            debit_call_args['commit'] = commit
            return original_debit(user_id, amount, source, description, reference_id, commit)

        with patch.object(service.besito_service, 'debit_besitos', mock_debit):
            service.advance_to_node(sample_user.id, node.id)

        # Verificar que debit_besitos fue llamado con commit=False
        assert 'commit' in debit_call_args
        assert debit_call_args['commit'] is False, (
            "advance_to_node debe llamar a debit_besitos con commit=False "
            "para mantener atomicidad (besitos + progreso en una transaccion)"
        )

    def test_advance_to_node_atomic_on_success_commits_both(self, db_session, sample_user):
        """Test que advance_to_node exitoso persiste besitos + progreso en una sola transaccion.

        Verifica que cuando advance_to_node tiene exito, tanto el debit de besitos
        como el progreso del usuario se persisten en la BD.
        """
        # Setup: crear nodo con costo
        node = StoryNode(
            title="Test Node",
            content="Test content",
            node_type=NodeType.NARRATIVE,
            cost_besitos=5,
            chapter=1,
            is_active=True,
        )
        db_session.add(node)
        db_session.commit()

        from models.models import BesitoBalance
        balance = BesitoBalance(
            user_id=sample_user.id,
            balance=100,
            total_earned=100,
            total_spent=0,
        )
        db_session.add(balance)
        db_session.commit()

        service = StoryService(db_session)

        # Ejecutar advance_to_node exitosamente
        success, _, progress = service.advance_to_node(sample_user.id, node.id)

        assert success is True
        assert progress is not None

        # Both besitos and progress are persisted atomically
        db_session.expire_all()
        from models.models import BesitoBalance as BB
        db_balance = db_session.query(BB).filter(BB.user_id == sample_user.id).first()
        assert db_balance.balance == 95, "Besitos deben estar debitados en la BD"

        db_session.expire(progress)
        updated_progress = db_session.query(UserStoryProgress).filter(
            UserStoryProgress.user_id == sample_user.id
        ).first()
        assert updated_progress.current_node_id == node.id, "Progreso debe estar guardado"

    def test_advance_to_node_removes_intermediate_commit(self, db_session, sample_user):
        """Test que advance_to_node NO tiene commits intermedios que rompan atomicidad.

        Verifica que debit_besitos se llama con commit=False para que el llamador
        controle el commit atomico al final.
        """
        node = StoryNode(
            title="Test Node",
            content="Test content",
            node_type=NodeType.NARRATIVE,
            cost_besitos=5,
            chapter=1,
            is_active=True,
        )
        db_session.add(node)
        db_session.commit()

        from models.models import BesitoBalance
        balance = BesitoBalance(
            user_id=sample_user.id,
            balance=100,
            total_earned=100,
            total_spent=0,
        )
        db_session.add(balance)
        db_session.commit()

        service = StoryService(db_session)

        # Spy on debit_besitos to verify commit=False is passed
        original_debit = service.besito_service.debit_besitos
        commit_values = []

        def spy_debit(*args, **kwargs):
            commit_values.append(kwargs.get('commit', True))
            return original_debit(*args, **kwargs)

        with patch.object(service.besito_service, 'debit_besitos', spy_debit):
            service.advance_to_node(sample_user.id, node.id)

        # debit_besitos debe ser llamado con commit=False
        assert any(v is False for v in commit_values), (
            "advance_to_node debe llamar a debit_besitos con commit=False "
            "para que el commit atomico se haga al final de advance_to_node"
        )


@pytest.mark.unit
class TestBigIntegerOverflow:
    """Tests para verificar que los campos de besitos usan BigInteger (Finding #5)."""

    def test_besito_balance_uses_biginteger(self):
        """Test que BesitoBalance.balance, total_earned, total_spent son BigInteger."""
        from models.models import BesitoBalance
        from sqlalchemy import BigInteger

        # Verificar que las columnas son BigInteger
        assert isinstance(BesitoBalance.balance.type, BigInteger)
        assert isinstance(BesitoBalance.total_earned.type, BigInteger)
        assert isinstance(BesitoBalance.total_spent.type, BigInteger)

    def test_besito_transaction_amount_uses_biginteger(self):
        """Test que BesitoTransaction.amount es BigInteger."""
        from models.models import BesitoTransaction
        from sqlalchemy import BigInteger

        assert isinstance(BesitoTransaction.amount.type, BigInteger)

    def test_broadcast_reaction_besitos_awarded_uses_biginteger(self):
        """Test que BroadcastReaction.besitos_awarded es BigInteger."""
        from models.models import BroadcastReaction
        from sqlalchemy import BigInteger

        assert isinstance(BroadcastReaction.besitos_awarded.type, BigInteger)


@pytest.mark.unit
class TestStoryServiceCRUD:
    def test_create_node(self, db_session, sample_admin):
        service = StoryService(db_session)
        node = service.create_node(
            title="Node A", content="Content A",
            node_type=NodeType.NARRATIVE, chapter=1,
            created_by=sample_admin.telegram_id
        )
        assert node.title == "Node A"
        assert node.node_type == NodeType.NARRATIVE

    def test_add_choice_to_node(self, db_session, sample_story_node):
        service = StoryService(db_session)
        choice = service.add_choice_to_node(
            sample_story_node.id, text="Choice 1",
            next_node_id=None, archetype_points=5
        )
        assert choice.node_id == sample_story_node.id
        assert choice.text == "Choice 1"
        assert choice.archetype_points == 5

    def test_get_node_choices(self, db_session, sample_story_node, sample_story_choice):
        service = StoryService(db_session)
        choices = service.get_node_choices(sample_story_node.id)
        assert any(c.id == sample_story_choice.id for c in choices)


@pytest.mark.unit
class TestStoryServiceArchetype:
    def test_calculate_archetype(self, db_session, sample_user):
        service = StoryService(db_session)
        progress = service.get_or_create_progress(sample_user.id)
        progress.explorador_points = 10
        progress.seductor_points = 5
        db_session.commit()
        archetype = service.calculate_archetype(progress)
        assert archetype == ArchetypeType.EXPLORADOR

    def test_get_user_archetype(self, db_session, sample_user):
        service = StoryService(db_session)
        progress = service.get_or_create_progress(sample_user.id)
        progress.archetype = ArchetypeType.MISTERIOSO
        db_session.commit()
        assert service.get_user_archetype(sample_user.id) == ArchetypeType.MISTERIOSO


@pytest.mark.unit
class TestStoryServiceBranching:
    def test_advance_to_node_with_choice_updates_archetype_points(self, db_session, sample_user):
        service = StoryService(db_session)
        from models.models import BesitoBalance
        bb = BesitoBalance(user_id=sample_user.id, balance=100, total_earned=100, total_spent=0)
        db_session.add(bb)
        db_session.commit()

        node_a = service.create_node("Decision", "Choose", NodeType.DECISION, chapter=1)
        node_b = service.create_node("Outcome B", "You chose B", NodeType.NARRATIVE, chapter=1)
        choice = service.add_choice_to_node(
            node_a.id, "Go to B", node_b.id,
            choice_archetype=ArchetypeType.EXPLORADOR, archetype_points=7
        )

        success, msg, progress = service.advance_to_node(sample_user.id, node_b.id, choice_id=choice.id)
        assert success is True
        db_session.refresh(progress)
        assert progress.current_node_id == node_b.id
        assert progress.explorador_points == 7

    def test_advance_to_node_deducts_besitos(self, db_session, sample_user):
        service = StoryService(db_session)
        from models.models import BesitoBalance
        bb = BesitoBalance(user_id=sample_user.id, balance=100, total_earned=100, total_spent=0)
        db_session.add(bb)
        db_session.commit()

        node = service.create_node("Costly", "Costs 10", NodeType.NARRATIVE, chapter=1, cost_besitos=10)
        success, msg, progress = service.advance_to_node(sample_user.id, node.id)
        assert success is True
        db_session.refresh(progress)
        assert progress.current_node_id == node.id
        assert service.besito_service.get_balance(sample_user.id) == 90


@pytest.mark.unit
class TestStoryServiceStats:
    def test_get_story_stats(self, db_session, sample_user):
        service = StoryService(db_session)
        progress = service.get_or_create_progress(sample_user.id)
        stats = service.get_story_stats()
        assert "total_nodes" in stats
        assert "total_chapters" in stats
        assert "total_users" in stats
        assert "completed_users" in stats
        assert "archetype_distribution" in stats
        assert "total_achievements" in stats
