"""Social media distribution — auto-post content to Twitter/X, Discord, Telegram, push."""

from app.services.social.twitter import (
    post_match_preview_tweet,
    post_value_bet_alert_tweet,
)
from app.services.social.discord import (
    post_match_preview_discord,
    post_value_bet_alert_discord,
)
from app.services.social.telegram import (
    post_match_preview_telegram,
    post_value_bet_alert_telegram,
)
from app.services.social.push import (
    push_match_preview,
    push_value_bet_alert,
    push_match_result,
)
from app.services.social.prediction_card import generate_prediction_card

__all__ = [
    "post_match_preview_tweet",
    "post_value_bet_alert_tweet",
    "post_match_preview_discord",
    "post_value_bet_alert_discord",
    "post_match_preview_telegram",
    "post_value_bet_alert_telegram",
    "push_match_preview",
    "push_value_bet_alert",
    "push_match_result",
    "generate_prediction_card",
]
