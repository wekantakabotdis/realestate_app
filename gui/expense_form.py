import sqlite3
from PySide6.QtWidgets import (
    QDialog, QFormLayout, QComboBox,
    QDateEdit, QLineEdit, QPushButton, QMessageBox,
    QRadioButton, QButtonGroup, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import QDate
from gui.db_utils import DBManager


class ExpenseFormDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowTitle('Add Transaction')
        self.resize(480, 320)
        layout = QFormLayout(self)

        # Address combo (editable for new)
        self.address_cb = QComboBox()
        self.address_cb.setEditable(True)
        self._load_addresses()
        layout.addRow('Address:', self.address_cb)

        # Date picker
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        layout.addRow('Date:', self.date_edit)

        # Transaction type (Income/Expense)
        type_layout = QHBoxLayout()
        self.type_group = QButtonGroup()
        self.income_radio = QRadioButton("Income")
        self.expense_radio = QRadioButton("Expense")
        self.expense_radio.setChecked(True)  # Default to expense
        self.type_group.addButton(self.income_radio)
        self.type_group.addButton(self.expense_radio)
        type_layout.addWidget(self.income_radio)
        type_layout.addWidget(self.expense_radio)
        type_layout.addStretch()
        layout.addRow('Type:', type_layout)

        # Category selection
        self.category_cb = QComboBox()
        self._setup_categories()
        layout.addRow('Category:', self.category_cb)

        # Connect type change to update categories
        self.income_radio.toggled.connect(self._update_categories)
        self.expense_radio.toggled.connect(self._update_categories)

        # Expense description
        self.expense_edit = QLineEdit()
        layout.addRow('Description:', self.expense_edit)

        # Recipient
        self.recipient_edit = QLineEdit()
        layout.addRow('Recipient:', self.recipient_edit)

        # Amount
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText('Enter amount')
        layout.addRow('Amount:', self.amount_edit)

        # Payment method (editable)
        self.payment_cb = QComboBox()
        self.payment_cb.setEditable(True)
        self.payment_cb.addItems([
            'Cash', 'Check', 'Credit Card',
            'Bank Transfer', 'Venmo', 'Zelle'
        ])
        layout.addRow('Payment Method:', self.payment_cb)

        # Save button
        btn_save = QPushButton('Save')
        btn_save.clicked.connect(self._save)
        layout.addRow(btn_save)

    def _setup_categories(self):
        self.income_categories = [
            'Rents received',
            'Royalties received'
        ]
        self.expense_categories = [
            'Advertising',
            'Auto and travel',
            'Cleaning and maintenance',
            'Commissions',
            'Insurance',
            'Legal and other professional fees',
            'Management fees',
            'Mortgage interest paid to banks',
            'Other interest',
            'Repairs',
            'Supplies',
            'Taxes',
            'Utilities',
            'Depreciation expense or depletion',
            'Other'
        ]
        self._update_categories()

    def _update_categories(self):
        self.category_cb.clear()
        if self.income_radio.isChecked():
            self.category_cb.addItems(self.income_categories)
        else:
            self.category_cb.addItems(self.expense_categories)

    def _load_addresses(self):
        conn = self.db.connect()
        cur = conn.cursor()
        cur.execute('SELECT address FROM houses')
        for (addr,) in cur.fetchall():
            self.address_cb.addItem(addr)
        conn.close()

    def _save(self):
        addr = self.address_cb.currentText().strip()
        date = self.date_edit.date().toString('yyyy-MM-dd')
        trans_type = 'income' if self.income_radio.isChecked() else 'expense'
        category = self.category_cb.currentText()
        exp = self.expense_edit.text().strip()
        rec = self.recipient_edit.text().strip()
        try:
            amt = float(self.amount_edit.text().replace('$', '').replace(',', ''))
            # Make amount negative for expenses
            if trans_type == 'expense':
                amt = -abs(amt)
            else:
                amt = abs(amt)
        except ValueError:
            QMessageBox.warning(self, 'Error', 'Amount must be a valid number')
            return
        pay = self.payment_cb.currentText().strip()

        conn = self.db.connect()
        cur = conn.cursor()
        # Insert or reuse house
        cur.execute('INSERT OR IGNORE INTO houses(address) VALUES(?)', (addr,))
        conn.commit()
        cur.execute('SELECT id FROM houses WHERE address=?', (addr,))
        hid = cur.fetchone()[0]
        # Insert transaction
        cur.execute(
            'INSERT INTO expenses(house_id, date, type, category, expense, recipient, amount, payment) VALUES(?,?,?,?,?,?,?,?)',
            (hid, date, trans_type, category, exp, rec, amt, pay)
        )
        conn.commit()
        conn.close()
        QMessageBox.information(self, 'Saved', 'Transaction recorded!')
        self.accept()
