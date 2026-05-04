"""
Smoke tests for trivia messages with Lucien voice.
Tests that STREAK_TEMPLATES and helper methods are properly implemented.
"""
import pytest
from services.game_service import GameService


class TestStreakTemplates:
    """Test that all STREAK_TEMPLATES keys exist and have variations."""

    @pytest.fixture
    def service(self):
        return GameService()

    def test_streak_templates_exist(self, service):
        """Verify all STREAK_TEMPLATES keys exist"""
        required_keys = [
            'entry_header', 'entry_promotion_bar', 'entry_promotion_progress',
            'entry_no_promotion', 'entry_footer_question',
            'correct_header', 'correct_number_sabe', 'correct_reward',
            'correct_encouragement', 'correct_next_streak',
            'incorrect_header', 'incorrect_answer_reveal', 'incorrect_footer',
            'tier_header', 'tier_unlock_bar', 'tier_unlock_icon', 'tier_unlock_text',
            'tier_options_prompt', 'tier_exit_message',
            'continue_header', 'continue_progress', 'continue_next_objective',
            'continue_warning', 'continue_prompt_question',
            'continue_wrong_header', 'continue_wrong_lost', 'continue_wrong_footer',
            'retire_success_header', 'retire_success_code', 'retire_success_promo',
            'retire_success_footer', 'retire_no_codes',
            'exit_header', 'exit_discount_waiting', 'exit_footer',
            'final_win_header', 'final_win_code', 'final_win_promo', 'final_win_footer',
            'limit_reached_header', 'limit_reached_body', 'limit_reached_footer'
        ]
        for key in required_keys:
            assert key in service.STREAK_TEMPLATES, f"Missing template: {key}"

    def test_templates_have_variations(self, service):
        """Verify each template has at least 2 variations"""
        for key, template_list in service.STREAK_TEMPLATES.items():
            assert isinstance(template_list, list), f"{key} should be a list"
            assert len(template_list) >= 2, f"{key} should have at least 2 variations"

    def test_progress_bar_builder(self, service):
        """Test progress bar generation"""
        bar = service._build_progress_bar(3, 5, 10)
        assert "▓" in bar
        assert "░" in bar
        assert len(bar) > 0

    def test_streak_promotion_text(self, service):
        """Test promotion text generation"""
        text = service._build_streak_promotion_text(2, 5, 50, "10 min")
        # Text includes progress bar, remaining streak info, and time
        assert "3" in text  # remaining streak
        assert "10 min" in text
        # Progress bar should contain block characters
        assert "░" in text or "▓" in text or "▒" in text

    def test_streak_promotion_text_no_time(self, service):
        """Test promotion text without time remaining"""
        text = service._build_streak_promotion_text(2, 5, 50)
        # Should contain remaining streak info
        assert "3" in text
        # No time indicator when time_remaining is None
        assert "⏳" not in text

    def test_select_template_returns_string(self, service):
        """Test that _select_template returns a string from list"""
        result = service._select_template(['a', 'b', 'c'])
        assert isinstance(result, str)
        assert result in ['a', 'b', 'c']