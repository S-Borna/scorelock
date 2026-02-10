"""Sentiment analysis service using Anthropic Claude.

Analyzes football news and social media content to generate
sentiment scores per team. Scores range from -1.0 (very negative)
to 1.0 (very positive), with a buzz_score indicating discussion volume.
"""

import json
import structlog
from datetime import datetime

from anthropic import AsyncAnthropic

from app.core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()

# ── Constants ──────────────────────────────────────────────

MAX_INPUT_LENGTH = 4000
MODEL_NAME = "claude-sonnet-4-20250514"

SYSTEM_PROMPT = """You are a football sentiment analyst. Analyze the provided text
about a football team and return a JSON object with these fields:

- "score": float from -1.0 (very negative) to 1.0 (very positive)
- "buzz_score": float from 0.0 (barely discussed) to 1.0 (major buzz)
- "summary": string, 1-2 sentence summary of the sentiment
- "key_factors": list of strings, main factors affecting sentiment

Only return valid JSON, nothing else."""


class SentimentAnalyzer:
    """Analyzes football sentiment using Anthropic Claude API."""

    def __init__(self) -> None:
        self.client: AsyncAnthropic | None = None

    def _get_client(self) -> AsyncAnthropic:
        """Lazy-initialize the Anthropic client."""
        if self.client is None:
            if not settings.anthropic_api_key:
                raise RuntimeError("ANTHROPIC_API_KEY not configured")
            self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self.client

    async def analyze_text(self, team_name: str, text: str) -> dict:
        """Analyze sentiment of text about a football team.

        Args:
            team_name: Name of the team being analyzed.
            text: News/social media text to analyze.

        Returns:
            Dict with score, buzz_score, summary, and key_factors.
        """
        client = self._get_client()
        truncated = text[:MAX_INPUT_LENGTH]

        prompt = (
            f"Analyze the sentiment of this football news/discussion about "
            f"{team_name}:\n\n{truncated}"
        )

        try:
            response = await client.messages.create(
                model=MODEL_NAME,
                max_tokens=500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )

            content = response.content[0].text.strip()
            result = json.loads(content)

            # Validate and clamp values
            score = max(-1.0, min(1.0, float(result.get("score", 0.0))))
            buzz = max(0.0, min(1.0, float(result.get("buzz_score", 0.5))))

            return {
                "score": round(score, 3),
                "buzz_score": round(buzz, 3),
                "summary": str(result.get("summary", "")),
                "key_factors": result.get("key_factors", []),
            }

        except json.JSONDecodeError as exc:
            logger.error("sentiment_json_parse_failed", team=team_name, error=str(exc))
            return {
                "score": 0.0,
                "buzz_score": 0.0,
                "summary": "Analysis failed: could not parse response",
                "key_factors": [],
            }
        except Exception as exc:
            logger.error("sentiment_analysis_failed", team=team_name, error=str(exc))
            raise

    async def analyze_match_context(
        self,
        home_team: str,
        away_team: str,
        news_items: list[str],
    ) -> dict:
        """Analyze sentiment for both teams in a match context.

        Args:
            home_team: Home team name.
            away_team: Away team name.
            news_items: List of news/social media snippets.

        Returns:
            Dict with home_sentiment and away_sentiment.
        """
        combined_text = "\n---\n".join(news_items)

        home_result = await self.analyze_text(home_team, combined_text)
        away_result = await self.analyze_text(away_team, combined_text)

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_sentiment": home_result,
            "away_sentiment": away_result,
            "analyzed_at": datetime.utcnow().isoformat(),
        }


# ── Singleton ──────────────────────────────────────────────

_analyzer: SentimentAnalyzer | None = None


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create the singleton sentiment analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SentimentAnalyzer()
    return _analyzer
