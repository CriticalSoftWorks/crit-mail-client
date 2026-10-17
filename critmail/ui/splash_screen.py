"""
CritMail UI - Animated SIGINT / Cyber-Envelope Splash Screen
Sleek modern dark aesthetic with animated curved telemetry waves, orbital radar arcs,
glowing CritMail shield emblem, and real-time boot sequence progress bar.
"""
import math
from pathlib import Path
from PyQt6.QtCore import Qt, QTimer, QPointF, QRectF, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QBrush, QLinearGradient, QRadialGradient,
    QPainterPath, QFont, QPolygonF, QImage
)
from PyQt6.QtWidgets import QWidget, QApplication

from critmail.config import APP_NAME, APP_VERSION
from critmail.ui.icon_factory import create_app_icon


BOOT_STAGES = [
    (18, "INITIALIZING SQLITE WAL CRYPTOGRAPHIC STORAGE..."),
    (38, "ENGAGING WINDOWS DPAPI HARDWARE CREDENTIAL VAULT..."),
    (60, "ARMING HTML SANITIZER, LINK GUARD & BEACON BLOCKER..."),
    (82, "CALIBRATING IMAP4 / POP3 / SMTP TLS 1.3 ENGINES..."),
    (100, "SIGINT TERMINAL READY // CLEARANCE VERIFIED"),
]


class CritMailSplashScreen(QWidget):
    """
    Frameless, hardware-accelerated custom QPainter splash screen with:
    - Smooth flowing curved Bezier/sine carrier waves in electric cyan, cobalt, and neon emerald
    - Rotating orbital SIGINT radar arcs around the central CritMail emblem
    - High-contrast typography and live initialization progress bar
    """
    finished = pyqtSignal()

    def __init__(self, duration_ms: int = 2100):
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setWindowIcon(create_app_icon())
        self.setFixedSize(680, 400)
        self._center_on_screen()

        self.duration_ms = max(600, duration_ms)
        self.elapsed_ms = 0
        self.tick_ms = 16  # ~60 FPS animation
        self.phase = 0.0
        self.progress = 0.0
        self.status_text = BOOT_STAGES[0][1]

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)

    def _center_on_screen(self):
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            x = geo.x() + (geo.width() - self.width()) // 2
            y = geo.y() + (geo.height() - self.height()) // 2
            self.move(x, y)

    def start(self):
        self.show()
        self.raise_()
        self._timer.start(self.tick_ms)

    def _on_tick(self):
        self.elapsed_ms += self.tick_ms
        self.phase += 0.085

        raw_pct = min(100.0, (self.elapsed_ms / float(self.duration_ms)) * 100.0)
        # Smooth ease-out curve for progress
        t = raw_pct / 100.0
        eased = 1.0 - pow(1.0 - t, 2.2)
        self.progress = min(100.0, eased * 100.0)

        for threshold, label in BOOT_STAGES:
            if self.progress <= threshold:
                self.status_text = label
                break
        else:
            self.status_text = BOOT_STAGES[-1][1]

        self.update()

        if self.elapsed_ms >= self.duration_ms:
            self._timer.stop()
            self.finished.emit()

    def mousePressEvent(self, event):
        # Allow user to click to skip splash early if desired
        if self.elapsed_ms > 350:
            self._timer.stop()
            self.finished.emit()

    def paintEvent(self, event):
        p = QPainter(self)
        draw_splash_scene(
            p,
            float(self.width()),
            float(self.height()),
            self.phase,
            self.progress,
            self.status_text
        )
        p.end()


def draw_splash_scene(
    p: QPainter,
    w: float,
    h: float,
    phase: float = 1.2,
    progress: float = 78.0,
    status_text: str = "SIGINT TERMINAL READY // CLEARANCE VERIFIED"
):
    """
    Renders the complete CritMail splash artwork onto any QPainter surface (live widget or PNG export).
    """
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    # 1. Deep Midnight Cyber-Navy Gradient Background
    bg = QLinearGradient(0, 0, w, h)
    bg.setColorAt(0.0, QColor("#040811"))
    bg.setColorAt(0.45, QColor("#091426"))
    bg.setColorAt(0.80, QColor("#0c1d36"))
    bg.setColorAt(1.0, QColor("#050b16"))
    p.fillRect(QRectF(0, 0, w, h), QBrush(bg))

    # 2. Ambient Radial Glow Behind Emblem & Title
    cx = w * 0.50
    cy = h * 0.39
    glow = QRadialGradient(QPointF(cx, cy), w * 0.44)
    glow.setColorAt(0.0, QColor(0, 229, 255, 52))
    glow.setColorAt(0.40, QColor(0, 128, 255, 24))
    glow.setColorAt(0.75, QColor(0, 240, 118, 10))
    glow.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.fillRect(QRectF(0, 0, w, h), QBrush(glow))

    # 3. Subtle Tactical Telemetry Grid
    grid_pen = QPen(QColor(24, 54, 92, 42), 1.0)
    p.setPen(grid_pen)
    step = 34
    for gx in range(0, int(w), step):
        p.drawLine(gx, 0, gx, int(h))
    for gy in range(0, int(h), step):
        p.drawLine(0, gy, int(w), gy)

    # 4. Sleek Curved Sweeping Background Horizon Arcs
    for idx, (arc_offset, col_hex, alpha, width_px) in enumerate([
        (-55.0, "#0077ff", 45, 1.5),
        (-20.0, "#00e5ff", 70, 2.0),
        (18.0, "#00f076", 48, 1.4),
    ]):
        arc_path = QPainterPath()
        y_start = h * 0.62 + arc_offset + math.sin(phase * 0.6 + idx) * 6.0
        y_ctrl1 = h * 0.22 + arc_offset - math.cos(phase * 0.5 + idx) * 14.0
        y_ctrl2 = h * 0.82 + arc_offset + math.sin(phase * 0.7 + idx) * 14.0
        y_end = h * 0.44 + arc_offset
        arc_path.moveTo(0.0, y_start)
        arc_path.cubicTo(w * 0.33, y_ctrl1, w * 0.66, y_ctrl2, w, y_end)

        c = QColor(col_hex)
        c.setAlpha(alpha)
        p.setPen(QPen(c, width_px))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(arc_path)

    # 5. Multi-Layered Animated Curved SIGINT Carrier Waves
    wave_configs = [
        # (amplitude, freq, speed_mult, y_base_ratio, color_hex, alpha, pen_width)
        (22.0, 0.013, 1.0, 0.52, "#00e5ff", 115, 2.2),
        (16.0, 0.018, -1.3, 0.55, "#0088ff", 85, 1.6),
        (12.0, 0.023, 1.6, 0.49, "#00f076", 75, 1.4),
    ]
    for amp, freq, spd, y_ratio, hex_c, alpha, pw in wave_configs:
        path = QPainterPath()
        base_y = h * y_ratio
        for x_int in range(0, int(w) + 6, 6):
            xf = float(x_int)
            # Envelope attenuation near edges for a sleek lens flare effect
            norm_x = xf / w
            envelope = math.sin(norm_x * math.pi)
            yf = base_y + math.sin(xf * freq + phase * spd) * amp * envelope
            if x_int == 0:
                path.moveTo(xf, yf)
            else:
                path.lineTo(xf, yf)
        wc = QColor(hex_c)
        wc.setAlpha(alpha)
        p.setPen(QPen(wc, pw))
        p.drawPath(path)

    # 6. Central Orbital Radar Rings & Curved Sweeping Arcs
    logo_cx = w * 0.50
    logo_cy = h * 0.31
    outer_r = 68.0
    mid_r = 56.0

    # Outer subtle ring
    p.setPen(QPen(QColor(0, 229, 255, 45), 1.2))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(logo_cx, logo_cy), outer_r, outer_r)

    # Rotating curved telemetry arcs
    deg_offset = int((phase * 42.0) % 360)
    arc_rect_outer = QRectF(logo_cx - outer_r, logo_cy - outer_r, outer_r * 2, outer_r * 2)
    p.setPen(QPen(QColor("#00e5ff"), 2.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawArc(arc_rect_outer, (deg_offset) * 16, 72 * 16)
    p.drawArc(arc_rect_outer, (deg_offset + 180) * 16, 72 * 16)

    arc_rect_mid = QRectF(logo_cx - mid_r, logo_cy - mid_r, mid_r * 2, mid_r * 2)
    p.setPen(QPen(QColor("#00f076"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    mid_ang = int(-deg_offset * 1.3)
    p.drawArc(arc_rect_mid, (mid_ang + 45) * 16, 55 * 16)
    p.drawArc(arc_rect_mid, (mid_ang + 225) * 16, 55 * 16)

    # 7. Central CritMail Cyber-Shield & Envelope Logo
    _draw_central_logo(p, logo_cx, logo_cy, radius=42.0)

    # 8. Sleek Header Telemetry Corner Brackets & Top Status Readout
    p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
    p.setPen(QColor("#29b6f6"))
    p.drawText(QRectF(18, 12, 320, 18), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
               "TIA // SIGINT COMMS KERNEL")
    p.setPen(QColor("#00f076"))
    p.drawText(QRectF(w - 320, 12, 302, 18), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
               f"BUILD {APP_VERSION} • DPAPI + TLS 1.3")

    # 9. Main Software Title & Subtitle
    title_y = h * 0.56
    title_font = QFont("Consolas", 25, QFont.Weight.Bold)
    title_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6.0)
    p.setFont(title_font)

    # Subtle cyan drop glow on title
    p.setPen(QColor(0, 229, 255, 65))
    p.drawText(QRectF(0, title_y + 1, w, 38), Qt.AlignmentFlag.AlignCenter, "CRITMAIL")

    p.setPen(QColor("#e8f4fc"))
    p.drawText(QRectF(0, title_y, w, 38), Qt.AlignmentFlag.AlignCenter, "CRITMAIL")

    # Subtitle badge
    sub_font = QFont("Consolas", 9, QFont.Weight.Bold)
    sub_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 2.2)
    p.setFont(sub_font)
    p.setPen(QColor("#00e5ff"))
    p.drawText(
        QRectF(0, title_y + 36, w, 20),
        Qt.AlignmentFlag.AlignCenter,
        "THE INTELLIGENCE AGENCY • SECURE COMMUNICATIONS TERMINAL"
    )

    # Secondary feature tagline
    tag_font = QFont("Consolas", 8)
    p.setFont(tag_font)
    p.setPen(QColor("#7da2c4"))
    p.drawText(
        QRectF(0, title_y + 56, w, 18),
        Qt.AlignmentFlag.AlignCenter,
        "IMAP4 / POP3 / SMTP SSL • AES-256-GCM CIPHER • ZERO-JS SANDBOX • LINK GUARD"
    )

    # 10. Progress Bar & Boot Sequence Status Readout
    bar_margin = 54.0
    bar_w = w - bar_margin * 2
    bar_h = 8.0
    bar_y = h - 48.0

    # Status text above bar
    p.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
    p.setPen(QColor("#00e5ff"))
    p.drawText(
        QRectF(bar_margin, bar_y - 20, bar_w * 0.82, 16),
        Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
        f"⚡ {status_text}"
    )
    p.setPen(QColor("#00f076"))
    p.drawText(
        QRectF(bar_margin, bar_y - 20, bar_w, 16),
        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        f"{int(progress):3d}%"
    )

    # Progress Track
    p.setPen(QPen(QColor("#1c3b63"), 1.0))
    p.setBrush(QColor("#07101e"))
    p.drawRect(QRectF(bar_margin, bar_y, bar_w, bar_h))

    # Progress Fill with Cyan -> Emerald Gradient
    fill_w = max(0.0, (bar_w - 2.0) * (progress / 100.0))
    if fill_w > 0:
        fill_grad = QLinearGradient(bar_margin, 0, bar_margin + bar_w, 0)
        fill_grad.setColorAt(0.0, QColor("#0077ff"))
        fill_grad.setColorAt(0.6, QColor("#00e5ff"))
        fill_grad.setColorAt(1.0, QColor("#00f076"))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(fill_grad))
        p.drawRect(QRectF(bar_margin + 1.0, bar_y + 1.0, fill_w, bar_h - 2.0))

    # 11. Outer Crisp Winamp 3 / SIGINT Double Frame
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(QColor("#00e5ff"), 1.5))
    p.drawRect(QRectF(1.0, 1.0, w - 2.0, h - 2.0))

    p.setPen(QPen(QColor("#173357"), 1.0))
    p.drawRect(QRectF(5.0, 5.0, w - 10.0, h - 10.0))


def _draw_central_logo(p: QPainter, cx: float, cy: float, radius: float = 42.0):
    """Draws the curved shield + cyber envelope + electric bolt emblem at (cx, cy)."""
    # Hexagonal / Curved Shield backdrop
    shield = QPainterPath()
    top = QPointF(cx, cy - radius)
    right_top = QPointF(cx + radius * 0.88, cy - radius * 0.45)
    right_bot = QPointF(cx + radius * 0.72, cy + radius * 0.48)
    bottom = QPointF(cx, cy + radius)
    left_bot = QPointF(cx - radius * 0.72, cy + radius * 0.48)
    left_top = QPointF(cx - radius * 0.88, cy - radius * 0.45)

    shield.moveTo(top)
    shield.quadTo(QPointF(cx + radius * 0.45, cy - radius * 0.82), right_top)
    shield.quadTo(QPointF(cx + radius * 0.92, cy + radius * 0.08), right_bot)
    shield.quadTo(QPointF(cx + radius * 0.40, cy + radius * 0.86), bottom)
    shield.quadTo(QPointF(cx - radius * 0.40, cy + radius * 0.86), left_bot)
    shield.quadTo(QPointF(cx - radius * 0.92, cy + radius * 0.08), left_top)
    shield.quadTo(QPointF(cx - radius * 0.45, cy - radius * 0.82), top)
    shield.closeSubpath()

    sh_grad = QLinearGradient(cx, cy - radius, cx, cy + radius)
    sh_grad.setColorAt(0.0, QColor("#173459"))
    sh_grad.setColorAt(0.5, QColor("#0c1c33"))
    sh_grad.setColorAt(1.0, QColor("#060e1b"))

    p.setPen(QPen(QColor("#00e5ff"), 2.2))
    p.setBrush(QBrush(sh_grad))
    p.drawPath(shield)

    # Cyber Envelope inside shield
    ew = radius * 1.12
    eh = radius * 0.74
    ex = cx - ew / 2.0
    ey = cy - eh / 2.0 + 2.0

    env_grad = QLinearGradient(ex, ey, ex, ey + eh)
    env_grad.setColorAt(0.0, QColor("#122a48"))
    env_grad.setColorAt(1.0, QColor("#081322"))
    p.setPen(QPen(QColor("#00e5ff"), 1.8))
    p.setBrush(QBrush(env_grad))
    p.drawRect(QRectF(ex, ey, ew, eh))

    # V-Flap
    flap = QPolygonF([
        QPointF(ex, ey),
        QPointF(cx, ey + eh * 0.58),
        QPointF(ex + ew, ey),
    ])
    p.drawPolyline(flap)

    # Electric Lightning Bolt Crest
    bolt = QPolygonF([
        QPointF(cx + radius * 0.10, cy - radius * 0.56),
        QPointF(cx - radius * 0.22, cy + radius * 0.04),
        QPointF(cx + radius * 0.02, cy + radius * 0.04),
        QPointF(cx - radius * 0.12, cy + radius * 0.62),
        QPointF(cx + radius * 0.28, cy - radius * 0.05),
        QPointF(cx + radius * 0.04, cy - radius * 0.05),
    ])
    bolt_grad = QLinearGradient(cx, cy - radius * 0.56, cx, cy + radius * 0.62)
    bolt_grad.setColorAt(0.0, QColor("#ffffff"))
    bolt_grad.setColorAt(0.45, QColor("#00f0ff"))
    bolt_grad.setColorAt(1.0, QColor("#00f076"))
    p.setPen(QPen(QColor("#050d18"), 1.2))
    p.setBrush(QBrush(bolt_grad))
    p.drawPolygon(bolt)


def export_splash_banner(output_path: Path, width: int = 840, height: int = 440) -> Path:
    """Renders the splash screen artwork to a high-resolution PNG file for README/Release assets."""
    img = QImage(width, height, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    draw_splash_scene(
        p,
        float(width),
        float(height),
        phase=1.35,
        progress=100.0,
        status_text="SIGINT TERMINAL ONLINE // AES-256-GCM + DPAPI VAULT ACTIVE"
    )
    p.end()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(str(output_path), "PNG")
    return output_path
