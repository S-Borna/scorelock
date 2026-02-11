"""Prediction card image generator — shareable social media images.

Generates a 1200×630 OG-image style card with:
  - Team names + league
  - ScoreLock prediction + probabilities
  - Value bet highlight
  - Branded footer

Uses Pillow for image generation (no external services needed).
"""

import io
from pathlib import Path

import structlog
from PIL import Image, ImageDraw, ImageFont

logger = structlog.get_logger()

# Card dimensions (OG image standard)
WIDTH = 1200
HEIGHT = 630

# Colors
BG_COLOR = (15, 23, 42)       # slate-900
ACCENT_COLOR = (16, 185, 129)  # emerald-500
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (148, 163, 184)    # slate-400
VALUE_GOLD = (245, 158, 11)   # amber-500


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Try to load a system font, fallback to default."""
    font_names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for font_path in font_names:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, size)
    return ImageFont.load_default()


def generate_prediction_card(
    home_team: str,
    away_team: str,
    league_name: str,
    kickoff: str,
    prediction: str,
    home_win_pct: float | None = None,
    draw_pct: float | None = None,
    away_win_pct: float | None = None,
    value_bet: str | None = None,
) -> bytes:
    """Generate a prediction card image.

    Returns:
        PNG image as bytes
    """
    img = Image.new("RGB", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Fonts
    font_title = _get_font(48, bold=True)
    font_subtitle = _get_font(24)
    font_body = _get_font(32)
    font_small = _get_font(20)
    font_brand = _get_font(28, bold=True)

    # ── Top accent bar ──
    draw.rectangle([(0, 0), (WIDTH, 6)], fill=ACCENT_COLOR)

    # ── League + kickoff ──
    draw.text((60, 40), f"🏆 {league_name}", fill=TEXT_GRAY, font=font_subtitle)
    draw.text((60, 75), kickoff, fill=TEXT_GRAY, font=font_small)

    # ── Teams ──
    match_text = f"{home_team}  vs  {away_team}"
    draw.text((60, 130), match_text, fill=TEXT_WHITE, font=font_title)

    # ── Prediction ──
    draw.text((60, 220), "🤖 ScoreLock-prognos", fill=ACCENT_COLOR, font=font_subtitle)
    draw.text((60, 260), prediction, fill=TEXT_WHITE, font=font_body)

    # ── Probabilities bar ──
    if home_win_pct is not None:
        y_bar = 330
        bar_width = WIDTH - 120
        bar_height = 40

        # Background bar
        draw.rectangle([(60, y_bar), (60 + bar_width, y_bar + bar_height)], fill=(30, 41, 59))

        # Home segment
        home_w = int(bar_width * home_win_pct / 100)
        draw.rectangle([(60, y_bar), (60 + home_w, y_bar + bar_height)], fill=ACCENT_COLOR)

        # Draw segment
        if draw_pct:
            draw_w = int(bar_width * draw_pct / 100)
            draw.rectangle(
                [(60 + home_w, y_bar), (60 + home_w + draw_w, y_bar + bar_height)],
                fill=TEXT_GRAY,
            )

        # Labels
        draw.text((60, y_bar + bar_height + 8), f"H: {home_win_pct:.0f}%", fill=ACCENT_COLOR, font=font_small)
        if draw_pct:
            draw.text((bar_width // 2, y_bar + bar_height + 8), f"D: {draw_pct:.0f}%", fill=TEXT_GRAY, font=font_small)
        if away_win_pct:
            bbox = draw.textbbox((0, 0), f"B: {away_win_pct:.0f}%", font=font_small)
            text_w = bbox[2] - bbox[0]
            draw.text(
                (60 + bar_width - text_w, y_bar + bar_height + 8),
                f"B: {away_win_pct:.0f}%",
                fill=(239, 68, 68),  # red-500
                font=font_small,
            )

    # ── Value bet ──
    if value_bet:
        y_vb = 430
        draw.text((60, y_vb), "💰 Value Bet", fill=VALUE_GOLD, font=font_subtitle)
        draw.text((60, y_vb + 35), value_bet, fill=TEXT_WHITE, font=font_body)

    # ── Bottom brand bar ──
    draw.rectangle([(0, HEIGHT - 60), (WIDTH, HEIGHT)], fill=(30, 41, 59))
    draw.text((60, HEIGHT - 48), "ScoreLock", fill=ACCENT_COLOR, font=font_brand)
    draw.text((250, HEIGHT - 42), "scorelock.saidborna.com", fill=TEXT_GRAY, font=font_small)

    # ── Export ──
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.getvalue()
