"""
CritMail Printing & PDF Export Engine
Supports direct hardware printing, print preview dialog, and clean PDF document generation.
"""
from pathlib import Path
from PyQt6.QtCore import Qt, QMarginsF
from PyQt6.QtGui import QTextDocument, QFont, QPageSize, QPageLayout
from PyQt6.QtWidgets import QDialog, QMessageBox, QFileDialog, QWidget
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog, QPageSetupDialog

from critmail.config import APP_NAME

def _create_printable_document(msg: dict) -> QTextDocument:
    """Formats an email into a clean, printable HTML document."""
    doc = QTextDocument()
    subject = msg.get("subject", "(No Subject)")
    sender = msg.get("sender", "")
    recipient = msg.get("recipient", "")
    cc = msg.get("cc", "")
    date = msg.get("date", "")
    body_html = msg.get("body_html", "")
    body_plain = msg.get("body_plain", "")

    header_html = f"""
    <div style="font-family: Arial, sans-serif; font-size: 11pt; border-bottom: 2px solid #000; padding-bottom: 12px; margin-bottom: 16px;">
        <h2 style="margin: 0 0 8px 0; color: #111;">{subject}</h2>
        <table style="width: 100%; font-size: 10pt; line-height: 1.4;">
            <tr><td style="width: 75px; font-weight: bold; color: #555;">From:</td><td>{sender}</td></tr>
            <tr><td style="font-weight: bold; color: #555;">To:</td><td>{recipient}</td></tr>
            {"<tr><td style='font-weight: bold; color: #555;'>Cc:</td><td>" + cc + "</td></tr>" if cc else ""}
            <tr><td style="font-weight: bold; color: #555;">Date:</td><td>{date}</td></tr>
        </table>
    </div>
    """

    if body_html:
        content_html = f"<div style='font-family: Arial, sans-serif; font-size: 10.5pt; line-height: 1.5;'>{body_html}</div>"
    else:
        escaped_plain = body_plain.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br>")
        content_html = f"<div style='font-family: Consolas, monospace; font-size: 10pt; line-height: 1.5; white-space: pre-wrap;'>{escaped_plain}</div>"

    footer_html = f"""
    <div style="margin-top: 24px; border-top: 1px solid #ccc; padding-top: 8px; font-family: sans-serif; font-size: 8pt; color: #777;">
        Printed from {APP_NAME} Secure Email Client
    </div>
    """

    doc.setHtml(header_html + content_html + footer_html)
    return doc

def print_message(parent_widget: QWidget, msg: dict):
    """Opens system Print Dialog to send message to physical or virtual printer."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    dialog = QPrintDialog(printer, parent_widget)
    dialog.setWindowTitle(f"Print Email - {msg.get('subject', 'CritMail')}")
    if dialog.exec() == QDialog.DialogCode.Accepted:
        doc = _create_printable_document(msg)
        doc.print(printer)

def print_preview_message(parent_widget: QWidget, msg: dict):
    """Displays standard Print Preview dialog."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    preview = QPrintPreviewDialog(printer, parent_widget)
    preview.setWindowTitle(f"Print Preview - {msg.get('subject', 'CritMail')}")
    preview.resize(900, 700)

    doc = _create_printable_document(msg)
    preview.paintRequested.connect(lambda p: doc.print(p))
    preview.exec()

def export_message_as_pdf(parent_widget: QWidget, msg: dict):
    """Exports message directly to a PDF document."""
    safe_subj = "".join(c if c.isalnum() or c in " -_" else "_" for c in (msg.get("subject") or "message"))[:40]
    file_path, _ = QFileDialog.getSaveFileName(
        parent_widget,
        "Export Email as PDF",
        f"{safe_subj}.pdf",
        "PDF Documents (*.pdf)"
    )
    if not file_path:
        return

    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(file_path)
    printer.setPageLayout(QPageLayout(QPageSize(QPageSize.PageSizeId.A4), QPageLayout.Orientation.Portrait, QMarginsF(15, 15, 15, 15)))

    doc = _create_printable_document(msg)
    doc.print(printer)

    QMessageBox.information(parent_widget, "PDF Export Complete", f"Email successfully saved to:\n{file_path}")

def show_page_setup(parent_widget: QWidget):
    """Opens printer page setup dialog."""
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    setup = QPageSetupDialog(printer, parent_widget)
    setup.exec()
