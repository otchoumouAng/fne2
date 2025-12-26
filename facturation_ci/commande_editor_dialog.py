from PyQt6.QtWidgets import QDialog, QMessageBox, QDialogButtonBox, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QDate

# Remplacer les imports pour Commande
from page._commande_editor import Ui_CommandeEditorDialog
from models.client import ClientModel
from models.product import ProductModel
from models.commande import CommandeModel
from core.theme import STYLESHEET

class CommandeEditorDialog(QDialog):
    def __init__(self, db_manager, commande_id=None, read_only=False, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.commande_id = commande_id
        # Utiliser CommandeModel
        self.commande_model = CommandeModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        self.product_model = ProductModel(self.db_manager)
        self.products = []

        # Utiliser l'UI de Commande
        self.ui = Ui_CommandeEditorDialog()
        self.ui.setupUi(self)
        self.setStyleSheet(STYLESHEET)

        self.setup_models()
        self.load_data()
        self.setup_connections()
        self._update_product_details()

        if self.commande_id:
            self._load_commande_data()

        if read_only:
            self._set_read_only()

    def setup_models(self):
        self.items_model = QStandardItemModel()
        self.items_model.setHorizontalHeaderLabels(
            ['Product ID', 'Produit', 'Description', 'Quantité', 'Prix U.', 'Taux TVA', 'Total HT']
        )
        self.ui.items_table_view.setModel(self.items_model)
        self.ui.items_table_view.setColumnHidden(0, True)
        self.ui.items_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_model.dataChanged.connect(self.update_totals)

    def setup_connections(self):
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.reject)
        self.ui.add_item_button.clicked.connect(self._add_item_to_table)
        self.ui.remove_item_button.clicked.connect(self.remove_item)
        self.ui.product_combobox.currentIndexChanged.connect(self._update_product_details)
        self.ui.quantity_spinbox.valueChanged.connect(self._update_product_details)

    def load_data(self):
        # Charger les clients
        clients = self.client_model.get_all()
        for client in clients:
            self.ui.client_combobox.addItem(client['name'], userData=client['id'])

        # Charger les produits
        self.products = self.product_model.get_all()
        self.ui.product_combobox.addItem("- Sélectionner un produit -", userData=None)
        for product in self.products:
            self.ui.product_combobox.addItem(product['name'], userData=product)

        # Mettre la date par défaut à aujourd'hui
        self.ui.date_commande_edit.setDate(QDate.currentDate())

    def _load_commande_data(self):
        self.setWindowTitle(f"Commande #{self.commande_id}")
        commande_data = self.commande_model.get_by_id(self.commande_id)
        if not commande_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger la commande ID {self.commande_id}.")
            self.reject()
            return

        details = commande_data['details']
        items = commande_data['items']

        # Client
        client_id = details['client_id']
        client_index = self.ui.client_combobox.findData(client_id)
        if client_index != -1:
            self.ui.client_combobox.setCurrentIndex(client_index)

        # Date
        self.ui.date_commande_edit.setDate(QDate.fromString(str(details['date_commande']), "yyyy-MM-dd"))

        # Lignes d'articles
        for item in items:
            total_ht = item['quantity'] * item['unit_price']
            row = [
                QStandardItem(str(item['product_id'])),
                QStandardItem(item['description']),
                QStandardItem(item['description']),
                # Utiliser le format :.10g
                QStandardItem(f"{item['quantity']:.10g}"),
                QStandardItem(f"{item['unit_price']:.10g}"),
                QStandardItem(f"{item['tax_rate']:.10g}"),
                QStandardItem(f"{total_ht:.10g}")
            ]
            self.items_model.appendRow(row)
        self.update_totals()

    def _set_read_only(self):
        self.setWindowTitle(f"Visualisation Commande #{self.commande_id}")
        self.ui.client_combobox.setEnabled(False)
        self.ui.date_commande_edit.setEnabled(False)
        self.ui.add_item_groupbox.setEnabled(False)
        self.ui.remove_item_button.setEnabled(False)
        self.ui.button_box.clear()
        self.ui.button_box.addButton(QDialogButtonBox.StandardButton.Close)

    def _update_product_details(self):
        product = self.ui.product_combobox.currentData()
        if product:
            price = float(product.get('unit_price', 0))
            tax_rate = float(product.get('tax_rate', 0))
            # Utiliser le format :.10g
            self.ui.price_value.setText(f"{price:.10g}")
            self.ui.tax_rate_value.setText(f"{tax_rate:.10g}%")
        else:
            # Utiliser un format simple pour zéro
            self.ui.price_value.setText("0")
            self.ui.tax_rate_value.setText("0%")

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
            QStandardItem(product['description']), 
            # Utiliser le format :.10g
            QStandardItem(f"{quantity:.10g}"),
            QStandardItem(f"{price:.10g}"), 
            QStandardItem(f"{tax_rate:.10g}"),
            QStandardItem(f"{total_ht:.10g}")
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
                # Arrondir la taxe de la ligne avant de l'ajouter
                row_total_tax = round(row_total_ht * (tax_rate / 100), 2)
                
                total_ht += row_total_ht
                total_tax += row_total_tax
            except (ValueError, TypeError, AttributeError):
                continue
        
        # Arrondir les totaux finaux pour être sûr
        total_ht = round(total_ht, 2)
        total_tax = round(total_tax, 2)
        # Recalculer le TTC à partir des totaux arrondis pour garantir la cohérence
        total_ttc = round(total_ht + total_tax, 2) 

        # Appliquer le format :.10g (général) avec séparateur de milliers
        self.ui.total_ht_value.setText(f"{total_ht:,.10g}".replace(",", " "))
        self.ui.total_tax_value.setText(f"{total_tax:,.10g}".replace(",", " "))
        self.ui.total_ttc_value.setText(f"{total_ttc:,.10g}".replace(",", " "))

    def get_data(self):
        client_id = self.ui.client_combobox.currentData()
        if not client_id:
            QMessageBox.warning(self, "Client manquant", "Veuillez sélectionner un client.")
            return None
        if self.items_model.rowCount() == 0:
            QMessageBox.warning(self, "Lignes manquantes", "Une commande doit contenir au moins une ligne.")
            return None

        total_ht_text = self.ui.total_ht_value.text().replace(" ", "").replace(",", ".")
        total_tax_text = self.ui.total_tax_value.text().replace(" ", "").replace(",", ".")
        total_ttc_text = self.ui.total_ttc_value.text().replace(" ", "").replace(",", ".")

        commande_details = {
            'client_id': client_id,
            'date_commande': self.ui.date_commande_edit.date().toString(Qt.DateFormat.ISODate),
            'total_ht': float(total_ht_text),
            'total_tva': float(total_tax_text),
            'total_ttc': float(total_ttc_text)
        }
        commande_items = []
        for row in range(self.items_model.rowCount()):
            item = {
                'product_id': int(self.items_model.item(row, 0).text()),
                'description': self.items_model.item(row, 2).text(),
                # CORRECTION : Utiliser float() au lieu de int() pour les quantités
                'quantity': float(self.items_model.item(row, 3).text()),
                'unit_price': float(self.items_model.item(row, 4).text()),
                'tax_rate': float(self.items_model.item(row, 5).text())
            }
            commande_items.append(item)
        return {'details': commande_details, 'items': commande_items}

    def accept(self):
        """
        Overrides the default accept to perform validation before closing.
        """
        if self.get_data():
            super().accept()
