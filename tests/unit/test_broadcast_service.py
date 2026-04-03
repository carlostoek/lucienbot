"""
Tests unitarios para BroadcastService.
"""
import pytest
from unittest.mock import patch, MagicMock

from services.broadcast_service import BroadcastService
from models.models import BroadcastReaction, BroadcastMessage, ReactionEmoji, BesitoBalance


@pytest.mark.unit
class TestBroadcastEmoji:
    """Tests para gestion de emojis de reaccion"""

    def test_create_reaction_emoji(self, db_session):
        """Test crear emoji de reaccion con besito_value"""
        service = BroadcastService(db_session)

        emoji = service.create_reaction_emoji(
            emoji="\U0001f48b",
            name="beso",
            besito_value=5
        )

        assert emoji.emoji == "\U0001f48b"
        assert emoji.name == "beso"
        assert emoji.besito_value == 5
        assert emoji.is_active is True

    def test_get_reaction_emoji_by_emoji(self, db_session, sample_reaction_emoji):
        """Test obtener emoji activo por caracter"""
        service = BroadcastService(db_session)

        emoji = service.get_reaction_emoji_by_emoji(sample_reaction_emoji.emoji)

        assert emoji is not None
        assert emoji.id == sample_reaction_emoji.id
        assert emoji.besito_value == sample_reaction_emoji.besito_value

    def test_update_emoji_value(self, db_session, sample_reaction_emoji):
        """Test actualizar valor de besitos de un emoji"""
        service = BroadcastService(db_session)

        result = service.update_emoji_value(sample_reaction_emoji.id, 10)

        assert result is True
        updated = service.get_reaction_emoji(sample_reaction_emoji.id)
        assert updated.besito_value == 10

    def test_toggle_emoji(self, db_session, sample_reaction_emoji):
        """Test activar/desactivar emoji"""
        service = BroadcastService(db_session)
        initial_state = sample_reaction_emoji.is_active

        result = service.toggle_emoji(sample_reaction_emoji.id)

        assert result is True
        updated = service.get_reaction_emoji(sample_reaction_emoji.id)
        assert updated.is_active is not initial_state

    def test_delete_emoji(self, db_session, sample_reaction_emoji):
        """Test eliminar emoji"""
        service = BroadcastService(db_session)
        emoji_id = sample_reaction_emoji.id

        result = service.delete_emoji(emoji_id)

        assert result is True
        assert service.get_reaction_emoji(emoji_id) is None


@pytest.mark.unit
class TestBroadcastMessage:
    """Tests para mensajes de broadcast"""

    def test_create_broadcast_message(self, db_session, sample_free_channel):
        """Test registrar mensaje de broadcast"""
        service = BroadcastService(db_session)

        broadcast = service.create_broadcast_message(
            message_id=11111,
            channel_id=sample_free_channel.channel_id,
            admin_id=987654321,
            text="Hello world",
            has_reactions=True
        )

        assert broadcast.message_id == 11111
        assert broadcast.channel_id == sample_free_channel.channel_id
        assert broadcast.admin_id == 987654321
        assert broadcast.text == "Hello world"
        assert broadcast.has_reactions is True

    def test_get_broadcast(self, db_session, sample_broadcast_message):
        """Test obtener broadcast por ID"""
        service = BroadcastService(db_session)

        broadcast = service.get_broadcast(sample_broadcast_message.id)

        assert broadcast is not None
        assert broadcast.id == sample_broadcast_message.id


@pytest.mark.unit
class TestBroadcastReactions:
    """Tests para reacciones y besitos"""

    def test_register_reaction_success(self, db_session, sample_user, sample_broadcast_message, sample_reaction_emoji):
        """Test registrar reaccion crea BroadcastReaction y acredita besitos"""
        service = BroadcastService(db_session)
        # Asegurar que el usuario tenga un balance inicial
        balance = BesitoBalance(
            user_id=sample_user.id,
            balance=0,
            total_earned=0,
            total_spent=0
        )
        db_session.add(balance)
        db_session.commit()

        reaction = service.register_reaction(
            sample_broadcast_message.id,
            sample_user.id,
            sample_reaction_emoji.id,
            username=sample_user.username
        )

        assert reaction is not None
        assert reaction.besitos_awarded == sample_reaction_emoji.besito_value
        assert reaction.broadcast_id == sample_broadcast_message.id
        assert reaction.user_id == sample_user.id

        # Verificar que se acreditaron besitos
        db_session.refresh(balance)
        assert balance.balance == sample_reaction_emoji.besito_value
        assert balance.total_earned == sample_reaction_emoji.besito_value

    def test_register_reaction_duplicate(self, db_session, sample_user, sample_broadcast_message, sample_reaction_emoji):
        """Test reaccion duplicada retorna None y no acredita doble"""
        service = BroadcastService(db_session)
        balance = BesitoBalance(
            user_id=sample_user.id,
            balance=0,
            total_earned=0,
            total_spent=0
        )
        db_session.add(balance)
        db_session.commit()

        # Primera reaccion
        reaction1 = service.register_reaction(
            sample_broadcast_message.id,
            sample_user.id,
            sample_reaction_emoji.id
        )
        assert reaction1 is not None

        # Segunda reaccion (duplicada)
        reaction2 = service.register_reaction(
            sample_broadcast_message.id,
            sample_user.id,
            sample_reaction_emoji.id
        )
        assert reaction2 is None

        # Verificar que no se acreditaron besitos dobles
        db_session.refresh(balance)
        assert balance.balance == sample_reaction_emoji.besito_value
        assert balance.total_earned == sample_reaction_emoji.besito_value


@pytest.mark.unit
class TestBroadcastQueries:
    """Tests para consultas de reacciones"""

    def test_get_reactions_by_broadcast(self, db_session, sample_user, sample_broadcast_message, sample_reaction_emoji):
        """Test obtener reacciones de un broadcast"""
        service = BroadcastService(db_session)
        balance = BesitoBalance(user_id=sample_user.id, balance=0, total_earned=0, total_spent=0)
        db_session.add(balance)
        db_session.commit()

        service.register_reaction(
            sample_broadcast_message.id,
            sample_user.id,
            sample_reaction_emoji.id
        )

        reactions = service.get_reactions_by_broadcast(sample_broadcast_message.id)

        assert len(reactions) == 1
        assert reactions[0].broadcast_id == sample_broadcast_message.id

    def test_get_user_reactions(self, db_session, sample_user, sample_broadcast_message, sample_reaction_emoji):
        """Test obtener reacciones de un usuario"""
        service = BroadcastService(db_session)
        balance = BesitoBalance(user_id=sample_user.id, balance=0, total_earned=0, total_spent=0)
        db_session.add(balance)
        db_session.commit()

        service.register_reaction(
            sample_broadcast_message.id,
            sample_user.id,
            sample_reaction_emoji.id
        )

        reactions = service.get_user_reactions(sample_user.id)

        assert len(reactions) == 1
        assert reactions[0].user_id == sample_user.id


@pytest.mark.unit
class TestBroadcastStats:
    """Tests para estadisticas de broadcast"""

    def test_get_broadcast_stats(self, db_session, sample_user, sample_broadcast_message, sample_reaction_emoji):
        """Test estadisticas con total reacciones, besitos y desglose por emoji"""
        service = BroadcastService(db_session)
        balance = BesitoBalance(user_id=sample_user.id, balance=0, total_earned=0, total_spent=0)
        db_session.add(balance)
        db_session.commit()

        # Crear dos reacciones del mismo usuario (una reentrada no permitida en realidad, simulamos una sola)
        service.register_reaction(
            sample_broadcast_message.id,
            sample_user.id,
            sample_reaction_emoji.id
        )

        stats = service.get_broadcast_stats(sample_broadcast_message.id)

        assert stats['total_reactions'] == 1
        assert stats['total_besitos_awarded'] == sample_reaction_emoji.besito_value
        assert stats['emoji_breakdown'][sample_reaction_emoji.emoji] == 1
        assert stats['unique_users'] == 1

    def test_get_broadcast_stats_not_found(self, db_session):
        """Test estadisticas para broadcast inexistente retorna dict vacio"""
        service = BroadcastService(db_session)

        stats = service.get_broadcast_stats(99999)

        assert stats == {}


@pytest.mark.unit
class TestBroadcastServiceRaceCondition:
    """Tests para verificar proteccion contra race conditions"""

    def test_register_reaction_uses_select_for_update(self, db_session, sample_broadcast_message, sample_reaction_emoji):
        """Test que register_reaction usa SELECT FOR UPDATE en BroadcastReaction"""
        service = BroadcastService(db_session)

        # Mock para query de BroadcastReaction (primer query)
        reaction_mock = MagicMock()
        reaction_filtered = MagicMock()
        reaction_with_lock = MagicMock()
        reaction_with_lock.first.return_value = None
        reaction_filtered.with_for_update.return_value = reaction_with_lock
        reaction_mock.filter.return_value = reaction_filtered

        # Mock para query de ReactionEmoji (segundo query en get_reaction_emoji)
        emoji_mock = MagicMock()
        emoji_mock.filter.return_value.first.return_value = sample_reaction_emoji

        # Mock para query de BesitoBalance (tercer query en credit_besitos)
        balance_mock = MagicMock()
        balance_filtered = MagicMock()
        balance_with_lock = MagicMock()
        balance_with_lock.first.return_value = None
        balance_filtered.with_for_update.return_value = balance_with_lock
        balance_mock.filter.return_value = balance_filtered

        with patch.object(db_session, 'query', side_effect=[reaction_mock, emoji_mock, balance_mock]):
            service.register_reaction(
                sample_broadcast_message.id,
                123456789,
                sample_reaction_emoji.id
            )
            reaction_filtered.with_for_update.assert_called()
