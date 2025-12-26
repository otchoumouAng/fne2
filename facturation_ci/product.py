import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._product import Ui_ProductPage
from models.product import ProductModel
from crud_dialog import CrudDialog

class ProductModule(QWidget):
    def __init__(self, db_manager, parent=None, user_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = user_data
        self.model = ProductModel(self.db_manager)

        self.ui = Ui_ProductPage()
        self.ui.setupUi(self)

        self.fields_config = [
            {'name': 'name', 'label': 'Nom', 'type': 'QLineEdit', 'required': True},
            {'name': 'description', 'label': 'Description', 'type': 'QTextEdit'},
            {'name': 'unit_price', 'label': 'Prix Unitaire', 'type': 'QLineEdit'},
            {'name': 'tax_rate', 'label': 'Taux de Taxe (%)', 'type': 'QLineEdit'},
        ]

        self.connect_signals()
        self.apply_permissions()
        self.load_products()

    def connect_signals(self):
        self.ui.new_button.clicked.connect(self.open_new_product_dialog)
        self.ui.edit_button.clicked.connect(self.open_edit_product_dialog)
        self.ui.delete_button.clicked.connect(self.delete_product)
        self.ui.table_view.doubleClicked.connect(self.handle_product_double_click)

    def apply_permissions(self):
        if not self.user_data:
            return
        perms = self.user_data.get('permissions', [])

        if 'products.create' not in perms:
            self.ui.new_button.setVisible(False)
        if 'products.edit' not in perms:
            self.ui.edit_button.setVisible(False)
        if 'products.delete' not in perms:
            self.ui.delete_button.setVisible(False)

        if 'products.edit' not in perms:
            self.ui.table_view.doubleClicked.disconnect(self.handle_product_double_click)

    def handle_product_double_click(self, index):
        """Ouvre le dialogue d'édition au double-clic."""
        self.open_edit_product_dialog()

    def load_products(self):
        products = self.model.get_all()
        self.set_products_in_view(products)

    def set_products_in_view(self, products):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['ID', 'Nom', 'Description', 'Prix Unitaire', 'Taux de Taxe'])
        self.ui.table_view.setModel(model)

        for product in products:
            row = [
                QStandardItem(str(product['id'])),
                QStandardItem(product['name']),
                QStandardItem(product['description']),
                QStandardItem(str(product['unit_price'])),
                QStandardItem(str(product['tax_rate']))
            ]
            for item in row:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            model.appendRow(row)

        self.ui.table_view.setColumnHidden(0, True)
        self.ui.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def get_selected_product_id(self):
        selected_indexes = self.ui.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        model = self.ui.table_view.model()
        id_index = model.index(selected_indexes[0].row(), 0)
        product_id = model.data(id_index)
        return int(product_id) if product_id else None

    def open_new_product_dialog(self):
        dialog = CrudDialog(
            mode='new',
            fields_config=self.fields_config,
            title="Nouveau Produit",
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if not new_data.get('name'):
                QMessageBox.warning(self, "Champ Requis", "Le nom du produit ne peut pas être vide.")
                return

            try:
                # Validate numeric fields
                float(new_data.get('unit_price', 0))
                float(new_data.get('tax_rate', 0))
            except ValueError:
                QMessageBox.warning(self, "Format Invalide", "Le prix unitaire et le taux de taxe doivent être des nombres.")
                return

            product_id, error = self.model.create(new_data)
            if error:
                QMessageBox.critical(self, "Erreur", f"Impossible de créer le produit: {error}")
            else:
                QMessageBox.information(self, "Succès", "Produit créé avec succès.")
                self.load_products()


    def open_edit_product_dialog(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner un produit à modifier.")
            return

        product_data = self.model.get_by_id(product_id)
        if not product_data:
            QMessageBox.critical(self, "Erreur", "Produit non trouvé.")
            return

        dialog = CrudDialog(
            mode='edit',
            fields_config=self.fields_config,
            title="Modifier le Produit",
            data=product_data,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_data()
            if not updated_data.get('name'):
                QMessageBox.warning(self, "Champ Requis", "Le nom du produit ne peut pas être vide.")
                return

            try:
                # Validate numeric fields
                float(updated_data.get('unit_price', 0))
                float(updated_data.get('tax_rate', 0))
            except ValueError:
                QMessageBox.warning(self, "Format Invalide", "Le prix unitaire et le taux de taxe doivent être des nombres.")
                return

            success, error = self.model.update(product_id, updated_data)
            if error:
                QMessageBox.critical(self, "Erreur", f"Impossible de mettre à jour le produit: {error}")
            else:
                QMessageBox.information(self, "Succès", "Produit mis à jour avec succès.")
                self.load_products()


    def delete_product(self):
        product_id = self.get_selected_product_id()
        if product_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner un produit à supprimer.")
            return

        product_data = self.model.get_by_id(product_id)
        if not product_data:
             QMessageBox.critical(self, "Erreur", "Produit non trouvé.")
             return

        reply = QMessageBox.question(
            self,
            "Confirmation de Suppression",
            f"Êtes-vous sûr de vouloir supprimer le produit '{product_data['name']}' ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self.model.delete(product_id)
            if error:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le produit: {error}")
            else:
                QMessageBox.information(self, "Succès", "Produit supprimé avec succès.")
                self.load_products()
