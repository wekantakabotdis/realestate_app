import os
import shutil
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMenuBar, QComboBox, QPushButton, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QLineEdit,
    QStyle, QStyleFactory, QLabel, QDialog, QInputDialog
)
from PySide6.QtGui import QAction, QIcon, QPalette, QColor, QFont
from PySide6.QtCore import Qt, QSettings
from gui.db_utils import DBManager
from gui.expense_form import ExpenseFormDialog
from gui.filter_dialog import FilterDialog
import sqlite3


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Real-Estate Tracker')
        self.resize(1200, 800)

        # Set Fusion style and customize palette for dark theme
        self.setStyle(QStyleFactory.create('Fusion'))
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(25, 25, 25))
        palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
        palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

        # Settings for persisting column widths
        self.settings = QSettings('RealEstateTracker', 'AppSettings')
        # Track last deleted items for undo
        self.last_deleted = None
        # Initialize active filters
        self.active_filters = {}

        # Database manager
        self.db_path = os.path.abspath('default.db')
        self.db = DBManager(self.db_path)
        self.db.init_db()

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Menu bar
        menu_bar = QMenuBar(self)
        menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #2d2d2d;
                color: white;
                border-bottom: 1px solid #1a1a1a;
            }
            QMenuBar::item {
                padding: 4px 8px;
                background: transparent;
            }
            QMenuBar::item:selected {
                background: #3d3d3d;
            }
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #1a1a1a;
                color: white;
            }
            QMenu::item {
                padding: 4px 20px;
            }
            QMenu::item:selected {
                background-color: #2a82da;
                color: white;
            }
        """)
        file_menu = menu_bar.addMenu('File')

        # File menu actions
        new_action = QAction('New', self)
        open_action = QAction('Open', self)
        saveas_action = QAction('Save As', self)
        undo_action = QAction('Undo', self)

        # Set icons for actions
        new_action.setIcon(self.style().standardIcon(QStyle.SP_FileIcon))
        open_action.setIcon(self.style().standardIcon(
            QStyle.SP_DialogOpenButton))
        saveas_action.setIcon(
            self.style().standardIcon(QStyle.SP_DialogSaveButton))
        undo_action.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))

        # Connect actions
        new_action.triggered.connect(self.new_file)
        open_action.triggered.connect(self.open_file)
        saveas_action.triggered.connect(self.save_as)
        undo_action.triggered.connect(self.undo)

        # Add actions to menu
        file_menu.addActions([new_action, open_action, saveas_action])
        file_menu.addSeparator()
        file_menu.addAction(undo_action)

        main_layout.setMenuBar(menu_bar)

        # Tabs: Summary and Details
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1a1a1a;
                background: #2d2d2d;
            }
            QTabBar::tab {
                background: #2d2d2d;
                border: 1px solid #1a1a1a;
                border-bottom: none;
                padding: 8px 16px;
                margin-right: 2px;
                color: white;
            }
            QTabBar::tab:selected {
                background: #1a1a1a;
                border-bottom: 1px solid #1a1a1a;
            }
            QTabBar::tab:hover {
                background: #3d3d3d;
            }
        """)

        # Summary tab
        summary_widget = QWidget()
        summary_layout = QVBoxLayout(summary_widget)
        summary_layout.setSpacing(10)

        # Summary table
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(2)
        self.summary_table.setHorizontalHeaderLabels(['Address', 'Total'])
        self.summary_table.setSortingEnabled(True)
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.horizontalHeader().setStretchLastSection(True)
        self.summary_table.cellDoubleClicked.connect(self._show_category_summary)
        # Make summary table read-only
        self.summary_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.summary_table.setStyleSheet("""
            QTableWidget { 
                border: 1px solid #1a1a1a;
                gridline-color: #3d3d3d;
                background: #1a1a1a;
                color: white;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 4px;
                border: 1px solid #1a1a1a;
                font-weight: bold;
                color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #2a82da;
                color: white;
            }
        """)
        summary_layout.addWidget(self.summary_table)

        # Total sum display
        total_layout = QHBoxLayout()
        total_layout.setContentsMargins(0, 10, 0, 0)
        total_label = QLabel('Total:')
        total_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        self.total_sum_label = QLabel('$0.00')
        self.total_sum_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        total_layout.addStretch()
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_sum_label)
        summary_layout.addLayout(total_layout)

        self.tabs.addTab(summary_widget, 'Summary')

        # Details tab
        details_widget = QWidget()
        details_layout = QVBoxLayout(details_widget)
        details_layout.setSpacing(10)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # Address selector
        self.addr_selector = QComboBox()
        self.addr_selector.setMinimumWidth(200)
        self.addr_selector.setStyleSheet("""
            QComboBox {
                padding: 4px;
                border: 1px solid #1a1a1a;
                border-radius: 3px;
                background: #2d2d2d;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(down-arrow.png);
                width: 12px;
                height: 12px;
            }
            QComboBox QAbstractItemView {
                background: #2d2d2d;
                color: white;
                selection-background-color: #2a82da;
            }
        """)
        self.addr_selector.currentTextChanged.connect(self.load_details)
        control_layout.addWidget(self.addr_selector)

        # Add rename address button
        rename_addr_btn = QPushButton('Rename Address')
        rename_addr_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        rename_addr_btn.setStyleSheet("""
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
        """)
        rename_addr_btn.clicked.connect(self._rename_address)
        control_layout.addWidget(rename_addr_btn)

        # Buttons
        add_btn = QPushButton('Add Expense')
        delete_exp_btn = QPushButton('Delete Expense')
        delete_addr_btn = QPushButton('Delete Address')
        clear_filters_btn = QPushButton('Clear Filters')

        # Set icons for buttons
        add_btn.setIcon(self.style().standardIcon(
            QStyle.SP_FileDialogNewFolder))
        delete_exp_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_addr_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        clear_filters_btn.setIcon(
            self.style().standardIcon(QStyle.SP_DialogResetButton))

        # Style buttons
        button_style = """
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
        """
        add_btn.setStyleSheet(button_style)
        delete_exp_btn.setStyleSheet(button_style)
        delete_addr_btn.setStyleSheet(button_style)
        clear_filters_btn.setStyleSheet(button_style)

        add_btn.clicked.connect(self.add_expense)
        delete_exp_btn.clicked.connect(self.delete_expense)
        delete_addr_btn.clicked.connect(self.delete_address)
        clear_filters_btn.clicked.connect(self.clear_filters)

        control_layout.addWidget(add_btn)
        control_layout.addWidget(delete_exp_btn)
        control_layout.addWidget(delete_addr_btn)
        control_layout.addWidget(clear_filters_btn)

        details_layout.addLayout(control_layout)

        self.details_table = QTableWidget()
        self.details_table.setColumnCount(8)
        self.details_table.setHorizontalHeaderLabels([
            'ID', 'Date', 'Type', 'Category', 'Description', 'Recipient', 'Amount', 'Payment'
        ])
        self.details_table.setSortingEnabled(True)
        self.details_table.setAlternatingRowColors(True)
        self.details_table.horizontalHeader().setStretchLastSection(True)
        # Set initial column widths
        self.details_table.setColumnWidth(0, 50)  # ID
        self.details_table.setColumnWidth(1, 100)  # Date
        self.details_table.setColumnWidth(2, 80)  # Type
        self.details_table.setColumnWidth(3, 150)  # Category
        self.details_table.setColumnWidth(4, 200)  # Description
        self.details_table.setColumnWidth(5, 150)  # Recipient
        self.details_table.setColumnWidth(6, 100)  # Amount
        self.details_table.setColumnWidth(7, 100)  # Payment
        # Make details table read-only
        self.details_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.details_table.setStyleSheet("""
            QTableWidget { 
                border: 1px solid #1a1a1a;
                gridline-color: #3d3d3d;
                background: #1a1a1a;
                color: white;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 4px;
                border: 1px solid #1a1a1a;
                font-weight: bold;
                color: white;
            }
            QHeaderView::section:filtered {
                background-color: #3d3d3d;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #2a82da;
                color: white;
            }
        """)
        # Connect header click event
        self.details_table.horizontalHeader().sectionClicked.connect(self._show_filter_dialog)
        details_layout.addWidget(self.details_table)

        # Add running total display
        total_layout = QHBoxLayout()
        total_layout.setContentsMargins(0, 10, 0, 0)
        total_label = QLabel('Running Total:')
        total_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        self.running_total_label = QLabel('$0.00')
        self.running_total_label.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                font-size: 14px;
            }
        """)
        total_layout.addStretch()
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.running_total_label)
        details_layout.addLayout(total_layout)

        self.tabs.addTab(details_widget, 'Details')

        main_layout.addWidget(self.tabs)

        # Load initial data and restore column widths
        self.load_summary()
        self.load_addresses()
        self._restore_column_widths()
        self._restore_summary_column_widths()

        # Connect column resize signals for persistence
        self.details_table.horizontalHeader().sectionResized.connect(self._save_column_width)
        self.summary_table.horizontalHeader().sectionResized.connect(
            self._save_summary_column_width)

    def _restore_column_widths(self):
        # Restore saved widths for details table
        for i in range(self.details_table.columnCount()):
            key = f'details_col_{i}_width'
            width = self.settings.value(key, type=int)
            if width:
                self.details_table.setColumnWidth(i, width)

    def _save_column_width(self, index, old, new):
        key = f'details_col_{index}_width'
        self.settings.setValue(key, new)

    def _restore_summary_column_widths(self):
        # Restore saved widths for summary table
        for i in range(self.summary_table.columnCount()):
            key = f'summary_col_{i}_width'
            width = self.settings.value(key, type=int)
            if width:
                self.summary_table.setColumnWidth(i, width)

    def _save_summary_column_width(self, index, old, new):
        key = f'summary_col_{index}_width'
        self.settings.setValue(key, new)

    def new_file(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'New Database', '', 'Database Files (*.db)'
        )
        if filepath:
            open(filepath, 'w').close()
            self.db_path = filepath
            self.db = DBManager(self.db_path)
            self.db.init_db()
            self.load_summary()
            self.load_addresses()

    def open_file(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, 'Open Database', '', 'Database Files (*.db)'
        )
        if filepath:
            self.db_path = filepath
            self.db = DBManager(self.db_path)
            self.db.init_db()
            self.load_summary()
            self.load_addresses()

    def save_as(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, 'Save Database As', '', 'Database Files (*.db)'
        )
        if filepath:
            shutil.copyfile(self.db_path, filepath)
            QMessageBox.information(
                self, 'Saved', f'Database saved to {filepath}'
            )

    def load_summary(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute('''
            SELECT h.address, 
                   COALESCE(SUM(CASE WHEN e.type = 'expense' THEN e.amount ELSE 0 END), 0) as expenses,
                   COALESCE(SUM(CASE WHEN e.type = 'income' THEN e.amount ELSE 0 END), 0) as income
            FROM houses h
            LEFT JOIN expenses e ON h.id = e.house_id
            GROUP BY h.id
        ''')
        rows = cur.fetchall()
        conn.close()

        # Calculate total income and expenses
        total_expenses = sum(row[1] for row in rows)
        total_income = sum(row[2] for row in rows)
        net_total = total_income + total_expenses  # expenses are already negative

        self.total_sum_label.setText(f'Net: ${net_total:,.2f} (Income: ${total_income:,.2f}, Expenses: ${abs(total_expenses):,.2f})')

        self.summary_table.setRowCount(len(rows))
        for row_index, (address, expenses, income) in enumerate(rows):
            self.summary_table.setItem(
                row_index, 0, QTableWidgetItem(address)
            )
            net = income + expenses  # expenses are already negative
            total_item = QTableWidgetItem(f'${net:,.2f}')
            total_item.setTextAlignment(Qt.AlignRight)
            self.summary_table.setItem(row_index, 1, total_item)

    def load_addresses(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute('SELECT address FROM houses')
        addresses = [r[0] for r in cur.fetchall()]
        conn.close()
        self.addr_selector.clear()
        self.addr_selector.addItems(addresses)
        if addresses:
            self.load_details(addresses[0])

    def _show_filter_dialog(self, column_index):
        # Get unique values for the column
        unique_values = set()
        for row in range(self.details_table.rowCount()):
            item = self.details_table.item(row, column_index)
            if item:
                unique_values.add(item.text())

        if not unique_values:
            return

        # Show filter dialog
        column_name = self.details_table.horizontalHeaderItem(
            column_index).text()
        dialog = FilterDialog(column_name, unique_values, self)
        if dialog.exec():
            selected_values = dialog.get_selected_values()
            # Update active filters
            if selected_values:
                self.active_filters[column_index] = selected_values
            else:
                self.active_filters.pop(column_index, None)

            # Apply all active filters
            self._apply_filters()

            # Update header style
            header = self.details_table.horizontalHeader()
            for col in range(self.details_table.columnCount()):
                if col in self.active_filters:
                    header.setSectionResizeMode(col, header.Stretch)
                    header.setStyleSheet("""
                        QHeaderView::section:filtered {
                            background-color: #3d3d3d;
                        }
                    """)
                else:
                    header.setStyleSheet("")

    def _apply_filters(self):
        # First, show all rows
        for row in range(self.details_table.rowCount()):
            self.details_table.setRowHidden(row, False)

        # Then apply each filter
        for column_index, selected_values in self.active_filters.items():
            for row in range(self.details_table.rowCount()):
                if not self.details_table.isRowHidden(row):
                    item = self.details_table.item(row, column_index)
                    if item:
                        self.details_table.setRowHidden(
                            row, item.text() not in selected_values
                        )

        self._update_running_total()

    def clear_filters(self):
        # Clear all filters
        self.active_filters.clear()

        # Show all rows
        for row in range(self.details_table.rowCount()):
            self.details_table.setRowHidden(row, False)

        # Reset header styles
        header = self.details_table.horizontalHeader()
        header.setStyleSheet("")

        self._update_running_total()

    def load_details(self, address):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute(
            'SELECT id FROM houses WHERE address = ?', (address,)
        )
        result = cur.fetchone()
        rows = []
        if result:
            house_id = result[0]
            cur.execute(
                'SELECT id, date, type, category, expense, recipient, amount, payment'
                ' FROM expenses WHERE house_id = ?',
                (house_id,)
            )
            rows = cur.fetchall()
        conn.close()
        self.details_table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            for col_index, value in enumerate(row_data):
                item = QTableWidgetItem(str(value))
                if col_index == 6:  # Amount column
                    item.setTextAlignment(Qt.AlignRight)
                    # Format amount with $ and commas
                    try:
                        amount = float(value)
                        # For display, show positive numbers with + for income
                        if amount >= 0:
                            item.setText(f'+${amount:,.2f}')
                        else:
                            item.setText(f'-${abs(amount):,.2f}')
                    except ValueError:
                        pass
                self.details_table.setItem(row_index, col_index, item)
        
        # Resize columns to content after loading data
        self.details_table.resizeColumnsToContents()
        # Ensure minimum widths for better readability
        min_widths = {
            0: 50,   # ID
            1: 100,  # Date
            2: 80,   # Type
            3: 150,  # Category
            4: 200,  # Description
            5: 150,  # Recipient
            6: 100,  # Amount
            7: 100   # Payment
        }
        for col, min_width in min_widths.items():
            if self.details_table.columnWidth(col) < min_width:
                self.details_table.setColumnWidth(col, min_width)
        
        self.load_summary()
        self._update_running_total()
        # Clear filters when loading new data
        self.clear_filters()

    def _update_running_total(self):
        total = 0.0
        for row in range(self.details_table.rowCount()):
            if not self.details_table.isRowHidden(row):
                amount_item = self.details_table.item(row, 6)  # Amount column
                if amount_item:
                    try:
                        amount = float(amount_item.text().replace('$', '').replace(',', ''))
                        total += amount
                    except ValueError:
                        pass
        self.running_total_label.setText(f'Net: ${total:,.2f}')

    def add_expense(self):
        dialog = ExpenseFormDialog(self.db, self)
        if dialog.exec():
            self.load_addresses()
            self.load_summary()

    def delete_expense(self):
        row = self.details_table.currentRow()
        if row < 0:
            QMessageBox.warning(
                self, 'Error', 'Please select an expense to delete.'
            )
            return
        expense_id = int(self.details_table.item(row, 0).text())
        reply = QMessageBox.question(
            self, 'Delete Expense',
            'Are you sure you want to delete this expense?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = self.db.connect()
            cur = conn.cursor()
            # Get expense data before deleting
            cur.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,))
            expense_data = cur.fetchone()
            if expense_data:
                self.last_deleted = ('expense', expense_data)
            cur.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
            conn.commit()
            conn.close()
            current_address = self.addr_selector.currentText()
            self.load_details(current_address)

    def delete_address(self):
        address = self.addr_selector.currentText()
        reply = QMessageBox.question(
            self, 'Delete Address',
            f'Are you sure you want to delete "{
                address}" and all its expenses?',
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            conn = self.db.connect()
            cur = conn.cursor()
            # Get house data before deleting
            cur.execute('SELECT * FROM houses WHERE address = ?', (address,))
            house_data = cur.fetchone()
            if house_data:
                # Get all expenses for this house
                cur.execute(
                    'SELECT * FROM expenses WHERE house_id = ?', (house_data[0],))
                expenses_data = cur.fetchall()
                self.last_deleted = ('address', (house_data, expenses_data))

            cur.execute(
                'DELETE FROM expenses WHERE house_id IN (SELECT id FROM houses WHERE address = ?)', (address,))
            cur.execute('DELETE FROM houses WHERE address = ?', (address,))
            conn.commit()
            conn.close()
            self.load_addresses()
            self.load_summary()

    def undo(self):
        if not self.last_deleted:
            QMessageBox.information(self, 'Undo', 'Nothing to undo')
            return

        action_type, data = self.last_deleted

        if action_type == 'expense':
            conn = self.db.connect()
            cur = conn.cursor()
            cur.execute(
                'INSERT OR IGNORE INTO expenses(id, house_id, date, expense, recipient, amount, payment) VALUES(?,?,?,?,?,?,?)',
                data
            )
            conn.commit()
            conn.close()
            self.load_details(self.addr_selector.currentText())
            self.load_summary()

        elif action_type == 'address':
            house_data, expenses_data = data
            conn = self.db.connect()
            cur = conn.cursor()
            # Restore house
            cur.execute(
                'INSERT OR IGNORE INTO houses(id, address) VALUES(?,?)',
                (house_data[0], house_data[1])
            )
            # Restore expenses
            for expense in expenses_data:
                cur.execute(
                    'INSERT OR IGNORE INTO expenses(id, house_id, date, expense, recipient, amount, payment) VALUES(?,?,?,?,?,?,?)',
                    expense
                )
            conn.commit()
            conn.close()
            self.load_addresses()
            self.load_summary()

        self.last_deleted = None

    def _show_category_summary(self, row, column):
        address = self.summary_table.item(row, 0).text()
        dialog = QDialog(self)
        dialog.setWindowTitle(f'Category Summary - {address}')
        dialog.resize(400, 500)
        layout = QVBoxLayout(dialog)

        # Create table for category summary
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(['Category', 'Income', 'Expenses'])
        table.setStyleSheet("""
            QTableWidget { 
                border: 1px solid #1a1a1a;
                gridline-color: #3d3d3d;
                background: #1a1a1a;
                color: white;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                padding: 4px;
                border: 1px solid #1a1a1a;
                font-weight: bold;
                color: white;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #2a82da;
                color: white;
            }
        """)

        # Get category summary data
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute('''
            SELECT e.category,
                   SUM(CASE WHEN e.type = 'income' THEN e.amount ELSE 0 END) as income,
                   SUM(CASE WHEN e.type = 'expense' THEN ABS(e.amount) ELSE 0 END) as expenses
            FROM houses h
            JOIN expenses e ON h.id = e.house_id
            WHERE h.address = ?
            GROUP BY e.category
            ORDER BY e.category
        ''', (address,))
        rows = cur.fetchall()
        conn.close()

        # Populate table
        table.setRowCount(len(rows))
        for row_idx, (category, income, expenses) in enumerate(rows):
            table.setItem(row_idx, 0, QTableWidgetItem(category))
            table.setItem(row_idx, 1, QTableWidgetItem(f'${income:,.2f}'))
            table.setItem(row_idx, 2, QTableWidgetItem(f'${expenses:,.2f}'))

        # Add totals row
        total_income = sum(row[1] for row in rows)
        total_expenses = sum(row[2] for row in rows)
        net = total_income - total_expenses

        table.setRowCount(len(rows) + 1)
        table.setItem(len(rows), 0, QTableWidgetItem('TOTAL'))
        table.setItem(len(rows), 1, QTableWidgetItem(f'${total_income:,.2f}'))
        table.setItem(len(rows), 2, QTableWidgetItem(f'${total_expenses:,.2f}'))

        # Add net row
        table.setRowCount(len(rows) + 2)
        table.setItem(len(rows) + 1, 0, QTableWidgetItem('NET'))
        net_item = QTableWidgetItem(f'${net:,.2f}')
        net_item.setForeground(QColor('green') if net >= 0 else QColor('red'))
        table.setItem(len(rows) + 1, 1, net_item)

        # Set column widths
        table.horizontalHeader().setStretchLastSection(True)
        for i in range(3):
            table.setColumnWidth(i, 120)

        layout.addWidget(table)

        # Add close button
        close_btn = QPushButton('Close')
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _rename_address(self):
        current_address = self.addr_selector.currentText()
        if not current_address:
            return

        new_address, ok = QInputDialog.getText(
            self, 'Rename Address',
            'Enter new address:',
            QLineEdit.Normal,
            current_address
        )

        if ok and new_address and new_address != current_address:
            conn = self.db.connect()
            cur = conn.cursor()
            try:
                cur.execute(
                    'UPDATE houses SET address = ? WHERE address = ?',
                    (new_address, current_address)
                )
                conn.commit()
                self.load_addresses()
                self.load_summary()
            except sqlite3.IntegrityError:
                QMessageBox.warning(
                    self, 'Error',
                    'An address with that name already exists.'
                )
            finally:
                conn.close()
