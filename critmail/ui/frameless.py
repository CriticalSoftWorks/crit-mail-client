"""
CritMail Frameless Window Engine - Winamp 3 Titlebar, Custom Icon & Full Menu Bar
Smooth dragging, 8-directional window edge resizing, miniature buttons, and integrated menu bar.
"""
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QMenuBar
)
from PyQt6.QtGui import QCursor, QMouseEvent
from critmail.ui.icon_factory import create_app_icon, create_titlebar_pixmap

RESIZE_MARGIN = 5

class WinampTitleBar(QFrame):
    """
    Winamp 3 Style Ultra-Slim Title Bar with custom cyber envelope icon and miniature control buttons.
    """
    def __init__(self, parent_window, title="CRITMAIL", subtitle="IMAP4 & POP3 // SSL/TLS"):
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("TitleBar")
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 4, 0)
        layout.setSpacing(5)

        # Custom Cyber Envelope & Shield Title Bar Icon
        self.lbl_icon = QLabel()
        self.lbl_icon.setPixmap(create_titlebar_pixmap(15))
        self.lbl_icon.setFixedSize(16, 16)
        layout.addWidget(self.lbl_icon)

        # Winamp style logo/status badge
        self.lbl_logo = QLabel(f"[ {title} ]")
        self.lbl_logo.setObjectName("TitleBarLabel")
        layout.addWidget(self.lbl_logo)

        self.lbl_sub = QLabel(f"// {subtitle}")
        self.lbl_sub.setObjectName("TitleBarSub")
        layout.addWidget(self.lbl_sub)

        layout.addStretch()

        # Miniature Winamp 3 Control Buttons
        self.btn_min = QPushButton("─")
        self.btn_min.setObjectName("BtnMin")
        self.btn_min.setProperty("class", "TitleBarBtn")
        self.btn_min.setToolTip("Minimize")
        self.btn_min.clicked.connect(self.parent_window.showMinimized)
        layout.addWidget(self.btn_min)

        self.btn_max = QPushButton("□")
        self.btn_max.setObjectName("BtnMax")
        self.btn_max.setProperty("class", "TitleBarBtn")
        self.btn_max.setToolTip("Maximize / Restore")
        self.btn_max.clicked.connect(self._toggle_maximize)
        layout.addWidget(self.btn_max)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("BtnClose")
        self.btn_close.setProperty("class", "TitleBarBtn")
        self.btn_close.setToolTip("Exit CritMail")
        self.btn_close.clicked.connect(self.parent_window.close)
        layout.addWidget(self.btn_close)

    def set_title(self, title: str, subtitle: str = ""):
        self.lbl_logo.setText(f"[ {title} ]")
        if subtitle:
            self.lbl_sub.setText(f"// {subtitle}")
        else:
            self.lbl_sub.setText("")

    def _toggle_maximize(self):
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
            self.btn_max.setText("□")
        else:
            self.parent_window.showMaximized()
            self.btn_max.setText("❐")

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._drag_pos and event.buttons() == Qt.MouseButton.LeftButton:
            if not self.parent_window.isMaximized():
                self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_maximize()


class FramelessWindow(QWidget):
    """
    Base Frameless Window with 8-directional edge resizing, Winamp 3 TitleBar, and MenuBar slot.
    """
    def __init__(self, title="CRITMAIL", subtitle="IMAP4 & POP3 // SSL/TLS"):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setWindowIcon(create_app_icon())
        
        self._resizing = False
        self._resize_edge = None
        self._drag_start_geometry = None
        self._drag_start_pos = None
        self.setMouseTracking(True)

        # Outer root layout
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(0, 0, 0, 0)
        self._root_layout.setSpacing(0)

        # Outer 1px frame container
        self.frame_container = QFrame(self)
        self.frame_container.setObjectName("MainFramelessContainer")
        self._root_layout.addWidget(self.frame_container)

        self._container_layout = QVBoxLayout(self.frame_container)
        self._container_layout.setContentsMargins(0, 0, 0, 0)
        self._container_layout.setSpacing(0)

        # 1. Winamp Title Bar
        self.title_bar = WinampTitleBar(self, title, subtitle)
        self._container_layout.addWidget(self.title_bar)

        # 2. Full Menu Bar directly below Title Bar
        self.menu_bar = QMenuBar(self.frame_container)
        self.menu_bar.setNativeMenuBar(False)
        self._container_layout.addWidget(self.menu_bar)

        # 3. Client content widget container
        self.client_widget = QWidget()
        self.client_widget.setObjectName("CentralWidget")
        self._container_layout.addWidget(self.client_widget, 1)

    def set_content_layout(self, layout):
        """Sets the layout inside the client area."""
        self.client_widget.setLayout(layout)

    def _get_resize_edges(self, pos: QPoint):
        rect = self.rect()
        edges = []
        if pos.x() <= RESIZE_MARGIN:
            edges.append("left")
        elif pos.x() >= rect.width() - RESIZE_MARGIN:
            edges.append("right")

        if pos.y() <= RESIZE_MARGIN:
            edges.append("top")
        elif pos.y() >= rect.height() - RESIZE_MARGIN:
            edges.append("bottom")

        return tuple(edges)

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton and not self.isMaximized():
            edges = self._get_resize_edges(event.pos())
            if edges:
                self._resizing = True
                self._resize_edge = edges
                self._drag_start_pos = event.globalPosition().toPoint()
                self._drag_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if not self.isMaximized():
            if self._resizing:
                delta = event.globalPosition().toPoint() - self._drag_start_pos
                geo = QRect(self._drag_start_geometry)

                if "left" in self._resize_edge:
                    geo.setLeft(min(geo.left() + delta.x(), geo.right() - self.minimumWidth()))
                elif "right" in self._resize_edge:
                    geo.setRight(max(geo.right() + delta.x(), geo.left() + self.minimumWidth()))

                if "top" in self._resize_edge:
                    geo.setTop(min(geo.top() + delta.y(), geo.bottom() - self.minimumHeight()))
                elif "bottom" in self._resize_edge:
                    geo.setBottom(max(geo.bottom() + delta.y(), geo.top() + self.minimumHeight()))

                self.setGeometry(geo)
                event.accept()
                return
            else:
                edges = self._get_resize_edges(event.pos())
                if ("left" in edges and "top" in edges) or ("right" in edges and "bottom" in edges):
                    self.setCursor(QCursor(Qt.CursorShape.SizeFDiagCursor))
                elif ("right" in edges and "top" in edges) or ("left" in edges and "bottom" in edges):
                    self.setCursor(QCursor(Qt.CursorShape.SizeBDiagCursor))
                elif "left" in edges or "right" in edges:
                    self.setCursor(QCursor(Qt.CursorShape.SizeHorCursor))
                elif "top" in edges or "bottom" in edges:
                    self.setCursor(QCursor(Qt.CursorShape.SizeVerCursor))
                else:
                    self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self._resizing = False
        self._resize_edge = None
        super().mouseReleaseEvent(event)
