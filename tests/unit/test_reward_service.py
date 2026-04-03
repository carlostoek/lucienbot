import pytest
from services.reward_service import RewardService
from models.models import Reward, RewardType, UserRewardHistory


@pytest.mark.unit
class TestRewardService:
    def test_stub(self, db_session):
        pass
