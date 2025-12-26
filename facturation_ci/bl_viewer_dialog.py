from PyQt6.QtWidgets import QDialog, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._bl_viewer_dialog import Ui_BLViewerDialog
from models.bl import BordereauLivraisonModel
from core.theme import STYLESHEET

class BLViewerDialog(QDialog):
    def __init__(self, db_manager, facture_id, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.facture_id = facture_id
        self.bl_model = BordereauLivraisonModel(self.db_manager)

        self.ui = Ui_BLViewerDialog()
        self.ui.setupUi(self)
        self.setStyleSheet(STYLESHEET)

        self.setup_connections()
        self.load_data()

    def setup_connections(self):
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.reject)

    def load_data(self):
        bl_data = self.bl_model.get_by_facture_id(self.facture_id)
        if not bl_data:
            # On pourrait afficher une QMessageBox ici, mais pour une vue simple,
            # on peut juste laisser les champs vides ou fermer.
            self.ui.value_code_bl.setText("Non trouvé")
            return

        details = bl_data['details']
        items = bl_data['items']

        # Remplir les détails du document
        self.ui.value_code_bl.setText(details.get('code_bl', 'N/A'))
        self.ui.value_date.setText(details.get('bl_date_creation', '').strftime('%Y-%m-%d %H:%M'))
        self.ui.value_facture.setText(details.get('code_facture', 'N/A'))

        # Remplir les infos client
        self.ui.value_client_name.setText(details.get('client_name', 'N/A'))
        self.ui.value_client_address.setText(details.get('client_address', 'N/A'))

        # Remplir la table des articles
        self.setup_items_table(items)

    def setup_items_table(self, items):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['ID Produit', 'Description', 'Quantité'])
        self.ui.items_table_view.setModel(model)
        self.ui.items_table_view.setColumnHidden(0, True)
        self.ui.items_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        for item in items:
            row = [
                QStandardItem(str(item['product_id'])),
                QStandardItem(item['description']),
                QStandardItem(str(item['quantity']))
            ]
            model.appendRow(row)

        # self.ui.items_table_view.resizeColumnsToContents()
