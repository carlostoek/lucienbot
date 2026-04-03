import pytest
from services.user_service import UserService
from models.models import User, UserRole


@pytest.mark.unit
class TestUserService:
    def test_create_user(self, db_session):
        service = UserService(db_session)
        user = service.create_user(telegram_id=999888777, username="newuser", first_name="New", last_name="User")
        assert user.telegram_id == 999888777
        assert user.username == "newuser"
        assert user.role == UserRole.USER
        assert user.is_active is True

    def test_get_user(self, db_session, sample_user):
        service = UserService(db_session)
        user = service.get_user(sample_user.telegram_id)
        assert user is not None
        assert user.id == sample_user.id

    def test_get_user_not_found(self, db_session):
        service = UserService(db_session)
        assert service.get_user(999999999) is None

    def test_get_or_create_user_creates_new(self, db_session):
        service = UserService(db_session)
        user = service.get_or_create_user(telegram_id=777666555, username="created")
        assert user.telegram_id == 777666555
        assert user.username == "created"

    def test_get_or_create_user_updates_info(self, db_session, sample_user):
        service = UserService(db_session)
        original_username = sample_user.username
        user = service.get_or_create_user(sample_user.telegram_id, username="updated_name", first_name="Updated")
        assert user.username == "updated_name"
        assert user.first_name == "Updated"

    def test_get_or_create_user_no_change_no_commit(self, db_session, sample_user):
        service = UserService(db_session)
        # Just verify it doesn't crash and returns same user
        user = service.get_or_create_user(sample_user.telegram_id, username=sample_user.username)
        assert user.id == sample_user.id

    def test_get_all_users(self, db_session, sample_user):
        service = UserService(db_session)
        users = service.get_all_users()
        assert any(u.id == sample_user.id for u in users)

    def test_get_admins(self, db_session, sample_admin):
        service = UserService(db_session)
        admins = service.get_admins()
        assert any(a.id == sample_admin.id for a in admins)

    def test_is_admin_true(self, db_session, sample_admin):
        service = UserService(db_session)
        assert service.is_admin(sample_admin.telegram_id) is True

    def test_is_admin_false(self, db_session, sample_user):
        service = UserService(db_session)
        assert service.is_admin(sample_user.telegram_id) is False

    def test_set_admin(self, db_session, sample_user):
        service = UserService(db_session)
        result = service.set_admin(sample_user.telegram_id)
        assert result is True
        assert service.is_admin(sample_user.telegram_id) is True

    def test_remove_admin(self, db_session, sample_admin):
        service = UserService(db_session)
        result = service.remove_admin(sample_admin.telegram_id)
        assert result is True
        assert service.is_admin(sample_admin.telegram_id) is False

    def test_deactivate_user(self, db_session, sample_user):
        service = UserService(db_session)
        result = service.deactivate_user(sample_user.telegram_id)
        assert result is True
        assert service.get_user(sample_user.telegram_id).is_active is False
