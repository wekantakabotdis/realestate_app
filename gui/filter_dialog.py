from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QCheckBox, QPushButton,
    QScrollArea, QWidget, QLabel, QHBoxLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


class FilterDialog(QDialog):
    def __init__(self, column_name, unique_values, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f'Filter by {column_name}')
        self.resize(300, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QCheckBox {
                color: white;
                padding: 4px;
            }
            QCheckBox:hover {
                background-color: #3d3d3d;
            }
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #1a1a1a;
                border-radius: 3px;
                background: #2d2d2d;
                color: white;
            }
            QPushButton:hover {
                background: #3d3d3d;
            }
            QPushButton:pressed {
                background: #1a1a1a;
            }
            QLabel#filterIcon {
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)

        # Add filter icon and label
        header_layout = QHBoxLayout()
        filter_icon = QLabel("🔍")
        filter_icon.setObjectName("filterIcon")
        header_layout.addWidget(filter_icon)

        search_label = QLabel(f"Filter by {column_name}:")
        search_label.setStyleSheet("color: white; font-weight: bold;")
        header_layout.addWidget(search_label)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Create scroll area for checkboxes
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: #2d2d2d;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #3d3d3d;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        # Create widget to hold checkboxes
        checkbox_widget = QWidget()
        checkbox_layout = QVBoxLayout(checkbox_widget)
        checkbox_layout.setSpacing(2)

        # Create checkboxes for each unique value
        self.checkboxes = {}
        for value in sorted(unique_values, key=str.lower):
            cb = QCheckBox(str(value))
            cb.setChecked(True)
            self.checkboxes[value] = cb
            checkbox_layout.addWidget(cb)

        scroll.setWidget(checkbox_widget)
        layout.addWidget(scroll)

        # Add buttons
        button_layout = QHBoxLayout()

        # Select All button
        select_all_btn = QPushButton("Select All")
        select_all_btn.clicked.connect(lambda: self._toggle_all(True))
        button_layout.addWidget(select_all_btn)

        # Deselect All button
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.clicked.connect(lambda: self._toggle_all(False))
        button_layout.addWidget(deselect_all_btn)

        # OK button
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        layout.addLayout(button_layout)

    def _toggle_all(self, checked):
        for cb in self.checkboxes.values():
            cb.setChecked(checked)

    def get_selected_values(self):
        return [value for value, cb in self.checkboxes.items() if cb.isChecked()]
