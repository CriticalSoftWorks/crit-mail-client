"""
CritMail Icon Factory - Winamp 3 Electric Blue Cyber Envelope & Security Shield Icon
Generates multi-resolution .ico for Windows Desktop/EXE and crisp QIcon/QPixmap for the Title Bar.
"""
from pathlib import Path
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QColor, QPen, QBrush,
    QLinearGradient, QPolygonF, QFont
)

def render_critmail_qimage(size: int = 256) -> QImage:
    """Renders the Winamp 3 Blue cyber envelope + lightning shield icon at any pixel size."""
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)

    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    s = float(size)

    # 1. Outer Square Frame (Zero rounded corners - pure Winamp 3 sharp bevel)
    bg_grad = QLinearGradient(0, 0, 0, s)
    bg_grad.setColorAt(0.0, QColor("#182c49"))
    bg_grad.setColorAt(0.5, QColor("#0d1829"))
    bg_grad.setColorAt(1.0, QColor("#070d17"))
    p.fillRect(QRectF(1, 1, s - 2, s - 2), QBrush(bg_grad))

    # Outer 1px-style neon cyan border
    border_w = max(1.0, s * 0.035)
    p.setPen(QPen(QColor("#00e5ff"), border_w))
    p.drawRect(QRectF(border_w / 2, border_w / 2, s - border_w, s - border_w))

    # Inner dark metallic bevel line
    inner_m = s * 0.08
    p.setPen(QPen(QColor("#1e3d66"), max(1.0, s * 0.015)))
    p.drawRect(QRectF(inner_m, inner_m, s - inner_m * 2, s - inner_m * 2))

    # 2. Cyber Envelope Body
    env_left = s * 0.14
    env_right = s * 0.86
    env_top = s * 0.25
    env_bot = s * 0.77
    env_w = env_right - env_left
    env_h = env_bot - env_top

    env_grad = QLinearGradient(env_left, env_top, env_left, env_bot)
    env_grad.setColorAt(0.0, QColor("#162c4a"))
    env_grad.setColorAt(1.0, QColor("#0a1424"))
    p.fillRect(QRectF(env_left, env_top, env_w, env_h), QBrush(env_grad))

    # Bottom fold lines
    p.setPen(QPen(QColor("#1c4470"), max(1.0, s * 0.025)))
    p.drawLine(QPointF(env_left, env_bot), QPointF(s * 0.42, s * 0.52))
    p.drawLine(QPointF(env_right, env_bot), QPointF(s * 0.58, s * 0.52))

    # Envelope outline & Top V-Flap in Electric Cyan
    flap_pen = QPen(QColor("#00e5ff"), max(1.2, s * 0.04))
    flap_pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    p.setPen(flap_pen)
    p.drawRect(QRectF(env_left, env_top, env_w, env_h))

    flap_poly = QPolygonF([
        QPointF(env_left, env_top),
        QPointF(s * 0.50, s * 0.56),
        QPointF(env_right, env_top)
    ])
    p.drawPolyline(flap_poly)

    # 3. Winamp-inspired Electric Lightning Bolt / Shield Emblem in Center-Right
    bolt = QPolygonF([
        QPointF(s * 0.55, s * 0.16),
        QPointF(s * 0.39, s * 0.50),
        QPointF(s * 0.51, s * 0.50),
        QPointF(s * 0.44, s * 0.84),
        QPointF(s * 0.64, s * 0.45),
        QPointF(s * 0.51, s * 0.45),
    ])
    bolt_grad = QLinearGradient(0, s * 0.16, 0, s * 0.84)
    bolt_grad.setColorAt(0.0, QColor("#ffffff"))
    bolt_grad.setColorAt(0.4, QColor("#00f0ff"))
    bolt_grad.setColorAt(1.0, QColor("#0088ff"))

    p.setPen(QPen(QColor("#07101c"), max(1.0, s * 0.025)))
    p.setBrush(QBrush(bolt_grad))
    p.drawPolygon(bolt)

    p.end()
    return img

def create_app_icon() -> QIcon:
    """Returns a multi-resolution QIcon for window, taskbar, and dialogs."""
    icon = QIcon()
    for sz in (16, 20, 24, 32, 48, 64, 128, 256):
        img = render_critmail_qimage(sz)
        icon.addPixmap(QPixmap.fromImage(img))
    return icon

def create_titlebar_pixmap(size: int = 16) -> QPixmap:
    """Returns a crisp pixmap for the Winamp 3 title bar."""
    return QPixmap.fromImage(render_critmail_qimage(size))

def generate_ico_files(assets_dir: Path) -> Path:
    """Generates multi-size critmail.ico and critmail.png on disk using Pillow."""
    from PIL import Image
    assets_dir.mkdir(parents=True, exist_ok=True)
    ico_path = assets_dir / "critmail.ico"
    png_path = assets_dir / "critmail.png"

    qimg = render_critmail_qimage(256)
    buffer = qimg.bits()
    buffer.setsize(256 * 256 * 4)
    # QImage ARGB32 is BGRA in memory on little-endian Windows
    pil_img = Image.frombuffer("RGBA", (256, 256), bytes(buffer), "raw", "BGRA", 0, 1)
    pil_img.save(png_path, format="PNG")
    pil_img.save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    )
    return ico_path
