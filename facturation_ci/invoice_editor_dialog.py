from PyQt6.QtWidgets import QDialog, QMessageBox, QDialogButtonBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QDate

from page._invoice_editor import Ui_InvoiceEditorDialog
from models.client import ClientModel
from models.product import ProductModel
from models.invoice import InvoiceModel

class InvoiceEditorDialog(QDialog):
    def __init__(self, db_manager, invoice_id=None, read_only=False, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.invoice_id = invoice_id
        self.invoice_model = InvoiceModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        self.product_model = ProductModel(self.db_manager)
        self.products = []

        self.ui = Ui_InvoiceEditorDialog()
        self.ui.setupUi(self)

        self.setup_models()
        self.load_data()
        self.setup_connections()
        self._update_product_details()

        if self.invoice_id:
            self._load_invoice_data()

        if read_only:
            self._set_read_only()

    def setup_models(self):
        self.items_model = QStandardItemModel()
        self.items_model.setHorizontalHeaderLabels(
            ['Product ID', 'Produit', 'Description', 'Quantité', 'Prix U.', 'Taux TVA', 'Total HT']
        )
        self.ui.items_table_view.setModel(self.items_model)
        self.ui.items_table_view.setColumnHidden(0, True)
        self.items_model.dataChanged.connect(self.update_totals)

    def setup_connections(self):
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.reject)
        self.ui.add_item_button.clicked.connect(self._add_item_to_table)
        self.ui.remove_item_button.clicked.connect(self.remove_item)
        self.ui.product_combobox.currentIndexChanged.connect(self._update_product_details)
        self.ui.quantity_spinbox.valueChanged.connect(self._update_product_details)

    def load_data(self):
        # Load clients
        clients = self.client_model.get_all()
        for client in clients:
            self.ui.client_combobox.addItem(client['name'], userData=client['id'])

        # Load products
        self.products = self.product_model.get_all()
        self.ui.product_combobox.addItem("- Sélectionner un produit -", userData=None)
        for product in self.products:
            self.ui.product_combobox.addItem(product['name'], userData=product)

    def _load_invoice_data(self):
        self.setWindowTitle(f"Facture #{self.invoice_id}")
        invoice_data = self.invoice_model.get_by_id(self.invoice_id)
        if not invoice_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger la facture ID {self.invoice_id}.")
            self.reject()
            return

        details = invoice_data['details']
        items = invoice_data['items']

        # Set client
        client_id = details['client_id']
        client_index = self.ui.client_combobox.findData(client_id)
        if client_index != -1:
            self.ui.client_combobox.setCurrentIndex(client_index)

        # Set dates
        self.ui.issue_date_edit.setDate(QDate.fromString(str(details['issue_date']), "yyyy-MM-dd"))
        self.ui.due_date_edit.setDate(QDate.fromString(str(details['due_date']), "yyyy-MM-dd"))

        # Populate items table
        for item in items:
            row = [
                QStandardItem(str(item['product_id'])),
                QStandardItem(item['description']), # In a real app, you'd look up the product name
                QStandardItem(item['description']),
                QStandardItem(str(item['quantity'])),
                QStandardItem(f"{item['unit_price']:.2f}"),
                QStandardItem(f"{item['tax_rate']:.2f}"),
                QStandardItem(f"{item['quantity'] * item['unit_price']:.2f}")
            ]
            self.items_model.appendRow(row)
        self.update_totals()

    def _set_read_only(self):
        self.setWindowTitle(f"Visualisation Facture #{self.invoice_id}")
        self.ui.client_combobox.setEnabled(False)
        self.ui.issue_date_edit.setEnabled(False)
        self.ui.due_date_edit.setEnabled(False)
        self.ui.add_item_groupbox.setEnabled(False)
        self.ui.remove_item_button.setEnabled(False)
        # Change button box to just have a "Close" button
        self.ui.button_box.clear()
        self.ui.button_box.addButton(QDialogButtonBox.StandardButton.Close)


    def _update_product_details(self):
        product = self.ui.product_combobox.currentData()
        if product:
            price = float(product.get('unit_price', 0))
            tax_rate = float(product.get('tax_rate', 0))
            self.ui.price_value.setText(f"{price:.2f}")
            self.ui.tax_rate_value.setText(f"{tax_rate:.2f}%")
        else:
            self.ui.price_value.setText("0.00")
            self.ui.tax_rate_value.setText("0.00%")

    def _add_item_to_table(self):
        product = self.ui.product_combobox.currentData()
        quantity = self.ui.quantity_spinbox.value()
        if not product:
            QMessageBox.warning(self, "Aucun produit", "Veuillez sélectionner un produit à ajouter.")
            return

        price = float(product['unit_price'])
        tax_rate = float(product['tax_rate'])
        total_ht = price * quantity
        row = [
            QStandardItem(str(product['id'])), QStandardItem(product['name']),
            QStandardItem(product['description']), QStandardItem(str(quantity)),
            QStandardItem(f"{price:.2f}"), QStandardItem(f"{tax_rate:.2f}"),
            QStandardItem(f"{total_ht:.2f}")
        ]
        self.items_model.appendRow(row)
        self.update_totals()
        self.ui.product_combobox.setCurrentIndex(0)
        self.ui.quantity_spinbox.setValue(1)

    def remove_item(self):
        selected_rows = self.ui.items_table_view.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner une ligne à supprimer.")
            return
        for index in sorted(selected_rows, reverse=True):
            self.items_model.removeRow(index.row())
        self.update_totals()

    def update_totals(self):
        total_ht = 0
        total_tax = 0
        for row in range(self.items_model.rowCount()):
            try:
                quantity = float(self.items_model.item(row, 3).text())
                price = float(self.items_model.item(row, 4).text())
                tax_rate = float(self.items_model.item(row, 5).text())
                row_total_ht = quantity * price
                row_total_tax = row_total_ht * (tax_rate / 100)
                total_ht += row_total_ht
                total_tax += row_total_tax
            except (ValueError, TypeError, AttributeError):
                continue
        total_ttc = total_ht + total_tax
        self.ui.total_ht_value.setText(f"{total_ht:,.2f}".replace(",", " "))
        self.ui.total_tax_value.setText(f"{total_tax:,.2f}".replace(",", " "))
        self.ui.total_ttc_value.setText(f"{total_ttc:,.2f}".replace(",", " "))

    def get_data(self):
        client_id = self.ui.client_combobox.currentData()
        if not client_id:
            QMessageBox.warning(self, "Client manquant", "Veuillez sélectionner un client.")
            return None
        if self.items_model.rowCount() == 0:
            QMessageBox.warning(self, "Lignes manquantes", "Une facture doit contenir au moins une ligne.")
            return None
        invoice_details = {
            'client_id': client_id,
            'issue_date': self.ui.issue_date_edit.date().toString(Qt.DateFormat.ISODate),
            'due_date': self.ui.due_date_edit.date().toString(Qt.DateFormat.ISODate),
            'total_amount': float(self.ui.total_ttc_value.text().replace(" ", ""))
        }
        invoice_items = []
        for row in range(self.items_model.rowCount()):
            item = {
                'product_id': int(self.items_model.item(row, 0).text()),
                'description': self.items_model.item(row, 2).text(),
                'quantity': float(self.items_model.item(row, 3).text()),
                'unit_price': float(self.items_model.item(row, 4).text()),
                'tax_rate': float(self.items_model.item(row, 5).text())
            }
            invoice_items.append(item)
        return {'details': invoice_details, 'items': invoice_items}

    def accept(self):
        """
        Overrides the default accept to perform validation before closing.
        The main module is responsible for saving the data.
        """
        if self.get_data():
            super().accept()
