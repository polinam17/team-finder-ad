import random
import uuid
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

AVATAR_SIZE = 256
# Спокойные светлые фоны, на которых хорошо видна тёмная буква.
BACKGROUND_COLORS = [
    "#D6E4FF",
    "#FFE8CC",
    "#D3F9D8",
    "#FCE4EC",
    "#E6E0FF",
    "#FFF3BF",
    "#CCF2F4",
    "#F1F3F5",
]
LETTER_COLOR = "#1F2937"
FONT_PATH = settings.BASE_DIR / "static" / "fonts" / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"


def _load_font(size):
    try:
        return ImageFont.truetype(str(FONT_PATH), size)
    except OSError:
        return ImageFont.load_default()


def generate_avatar(name):
    """Возвращает ContentFile с PNG: первая буква имени на однотонном фоне."""
    letter = (name or "?").strip()[:1].upper() or "?"
    image = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), random.choice(BACKGROUND_COLORS))
    draw = ImageDraw.Draw(image)
    draw.text(
        (AVATAR_SIZE / 2, AVATAR_SIZE / 2),
        letter,
        font=_load_font(int(AVATAR_SIZE * 0.55)),
        fill=LETTER_COLOR,
        anchor="mm",
    )
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"avatar_{uuid.uuid4()}.png")
