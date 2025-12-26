from PyQt6.QtWidgets import QDialog, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._avoir_viewer_dialog import Ui_AvoirViewerDialog
from models.avoir import FactureAvoirModel
from core.theme import STYLESHEET

class AvoirViewerDialog(QDialog):
    def __init__(self, db_manager, avoir_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.avoir_id = avoir_id
        self.avoir_model = FactureAvoirModel(self.db_manager)

        self.ui = Ui_AvoirViewerDialog()
        self.ui.setupUi(self)
        self.setStyleSheet(STYLESHEET)

        self.ui.button_box.accepted.connect(self.accept)
        self.load_data()

    def load_data(self):
        avoir_data = self.avoir_model.get_by_id(self.avoir_id)
        if not avoir_data:
            self.ui.value_code_avoir.setText("Non trouvé")
            return

        # Remplir les détails du document
        self.ui.value_code_avoir.setText(avoir_data.get('code_avoir', 'N/A'))
        self.ui.value_date.setText(avoir_data.get('date_creation', '').strftime('%Y-%m-%d'))
        self.ui.value_facture_origine.setText(avoir_data.get('code_facture_origine', 'N/A'))

        # Remplir les totaux
        self.ui.value_total_ht.setText(f"{avoir_data.get('total_ht', 0):.2f}")
        self.ui.value_total_tax.setText(f"{avoir_data.get('total_tva', 0):.2f}")
        self.ui.value_total_ttc.setText(f"{avoir_data.get('total_ttc', 0):.2f}")

        # Remplir la table des articles
        self.setup_items_table(avoir_data.get('lignes_avoir', []))

    def setup_items_table(self, items):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['ID Produit', 'Description', 'Quantité', 'Prix U.'])
        self.ui.items_table_view.setModel(model)
        self.ui.items_table_view.setColumnHidden(0, True)
        self.ui.items_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for item in items:
            row = [
                QStandardItem(str(item['product_id'])),
                QStandardItem(item['description']),
                QStandardItem(str(item['quantity'])),
                QStandardItem(f"{item['unit_price']:.2f}")
            ]
            model.appendRow(row)

        # self.ui.items_table_view.resizeColumnsToContents()
