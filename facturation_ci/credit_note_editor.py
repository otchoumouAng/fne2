from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem

from page._credit_note_editor import Ui_CreditNoteEditorDialog
from models.facture import FactureModel
from core.theme import STYLESHEET

class CreditNoteEditorDialog(QDialog):
    def __init__(self, db_manager, facture_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.facture_id = facture_id
        self.facture_model = FactureModel(self.db_manager)
        self.original_invoice_data = None

        self.ui = Ui_CreditNoteEditorDialog()
        self.ui.setupUi(self)
        self.setStyleSheet(STYLESHEET)

        self.setup_ui()
        self.setup_connections()
        self.load_original_invoice()

    def setup_ui(self):
        # Ajouter le bouton de génération
        self.generate_button = self.ui.button_box.addButton("Générer l'Avoir", QDialogButtonBox.ButtonRole.AcceptRole)

        # Configurer le modèle de la table
        self.items_model = QStandardItemModel()
        self.items_model.setHorizontalHeaderLabels(['ID Commande Item', 'ID Produit', 'Description', 'Quantité', 'Prix U.', 'Taux TVA'])
        self.ui.items_table_view.setModel(self.items_model)
        self.ui.items_table_view.setColumnHidden(0, True) # Masquer ID Commande Item
        self.ui.items_table_view.setColumnHidden(1, True) # Masquer ID Produit
        self.ui.items_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def setup_connections(self):
        self.ui.remove_item_button.clicked.connect(self.remove_selected_item)
        self.generate_button.clicked.connect(self.accept)
        self.ui.button_box.rejected.connect(self.reject)

    def load_original_invoice(self):
        self.original_invoice_data = self.facture_model.get_by_id_for_printing(self.facture_id)
        if not self.original_invoice_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger la facture d'origine ID {self.facture_id}.")
            self.reject()
            return

        details = self.original_invoice_data['details']
        items = self.original_invoice_data['items']

        # Remplir les champs d'en-tête
        self.ui.value_code_facture.setText(details.get('code_facture', 'N/A'))
        self.ui.value_client.setText(details.get('client_name', 'N/A'))

        # Remplir la table avec les articles d'origine
        for item in items:
            row = [
                QStandardItem(str(item['id'])), # ID Commande Item
                QStandardItem(str(item['product_id'])),
                QStandardItem(item['description']),
                QStandardItem(f"{item['quantity']:.0f}"),
                QStandardItem(f"{item['unit_price']:.3f}"),
                QStandardItem(f"{item['tax_rate']:.3f}")
            ]
            self.items_model.appendRow(row)

        # self.ui.items_table_view.resizeColumnsToContents()
        self.update_totals()

    def remove_selected_item(self):
        selected_rows = self.ui.items_table_view.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner une ligne à retirer.")
            return

        # Supprimer en ordre inverse pour éviter les problèmes d'index
        for index in sorted(selected_rows, reverse=True):
            self.items_model.removeRow(index.row())

        self.update_totals()

    def update_totals(self):
        total_ht = 0
        total_tva = 0
        for row in range(self.items_model.rowCount()):
            try:
                quantity = float(self.items_model.item(row, 3).text())
                price = float(self.items_model.item(row, 4).text())
                tax_rate = float(self.items_model.item(row, 5).text())

                row_total_ht = quantity * price
                row_total_tva = row_total_ht * (tax_rate / 100)

                total_ht += row_total_ht
                total_tva += row_total_tva
            except (ValueError, TypeError, AttributeError):
                continue

        total_ttc = total_ht + total_tva
        self.ui.value_total_ht.setText(f"{total_ht:,.3f}".replace(",", " "))
        self.ui.value_total_tax.setText(f"{total_tva:,.3f}".replace(",", " "))
        self.ui.value_total_ttc.setText(f"{total_ttc:,.3f}".replace(",", " "))

    def get_data(self):
        """Retourne les données nécessaires pour créer l'enregistrement de l'avoir."""
        if self.items_model.rowCount() == len(self.original_invoice_data['items']):
             QMessageBox.warning(self, "Aucune modification", "Vous devez retirer au moins un article pour créer un avoir.")
             return None

        avoir_items = []
        for row in range(self.items_model.rowCount()):
            item = {
                'commande_item_id': int(self.items_model.item(row, 0).text()),
                'product_id': int(self.items_model.item(row, 1).text()),
                'description': self.items_model.item(row, 2).text(),
                'quantity': int(self.items_model.item(row, 3).text()),
                'unit_price': float(self.items_model.item(row, 4).text()),
                'tax_rate': float(self.items_model.item(row, 5).text())
            }
            avoir_items.append(item)

        totals = {
            'total_ht': float(self.ui.value_total_ht.text().replace(" ", "")),
            'total_tva': float(self.ui.value_total_tax.text().replace(" ", "")),
            'total_ttc': float(self.ui.value_total_ttc.text().replace(" ", ""))
        }

        return {
            'original_facture_id': self.facture_id,
            'code_facture_origine': self.original_invoice_data['details']['code_facture'],
            'avoir_items': avoir_items,
            'totals': totals
        }

    def accept(self):
        if self.get_data():
            super().accept()
