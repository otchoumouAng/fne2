from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QPushButton, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import QSortFilterProxyModel, Qt

from page._new_invoice_dialog import Ui_NewInvoiceDialog
from models.commande import CommandeModel
from models.client import ClientModel
from core.theme import STYLESHEET

class NewInvoiceDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.commande_model = CommandeModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        
        self.ui = Ui_NewInvoiceDialog()
        self.ui.setupUi(self)
        self.setStyleSheet(STYLESHEET)

        # 1. Créer le bouton AVANT de connecter les signaux
        self.generate_button = self.ui.button_box.addButton("Générer la facture", QDialogButtonBox.ButtonRole.AcceptRole)
        self.generate_button.setEnabled(False)

        self.master_commandes = []
        self.selected_commande_id = None

        self.setup_model()
        self.setup_filters()
        self.load_unvoiced_commandes()
        self.setup_connections()

    def setup_model(self):
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(['ID', 'Code Commande', 'Client', 'Date', 'Total TTC'])

        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)

        self.ui.commandes_table_view.setModel(self.proxy_model)
        self.ui.commandes_table_view.setColumnHidden(0, True)
        self.ui.commandes_table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def setup_filters(self):
        # Clients
        clients = self.client_model.get_all()
        self.ui.client_filter_combo.addItem("Tous les clients", userData=None)
        for client in clients:
            self.ui.client_filter_combo.addItem(client['name'], userData=client['id'])

        # Dates et Codes (seront remplis dans load_unvoiced_commandes)
        self.ui.date_filter_combo.addItem("Toutes les dates", userData=None)
        self.ui.commande_code_filter_combo.addItem("Tous les codes", userData=None)

    def setup_connections(self):
        self.ui.commandes_table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.generate_button.clicked.connect(self.accept)
        self.ui.client_filter_combo.currentIndexChanged.connect(self.apply_filters)
        self.ui.date_filter_combo.currentIndexChanged.connect(self.apply_filters)
        self.ui.commande_code_filter_combo.currentIndexChanged.connect(self.apply_filters)

    def load_unvoiced_commandes(self):
        self.unvoiced_commandes = self.commande_model.get_all_unvoiced()
        self.model.removeRows(0, self.model.rowCount())

        # Remplir les filtres de date et code
        self.ui.date_filter_combo.blockSignals(True)
        self.ui.commande_code_filter_combo.blockSignals(True)

        unique_dates = sorted(list(set(cmd['date_commande'].strftime('%Y-%m-%d') for cmd in self.unvoiced_commandes)), reverse=True)
        unique_codes = sorted(list(set(cmd['code_commande'] for cmd in self.unvoiced_commandes)))

        self.ui.date_filter_combo.clear()
        self.ui.date_filter_combo.addItem("Toutes les dates", userData=None)
        for date in unique_dates:
            self.ui.date_filter_combo.addItem(date)

        self.ui.commande_code_filter_combo.clear()
        self.ui.commande_code_filter_combo.addItem("Tous les codes", userData=None)
        for code in unique_codes:
            self.ui.commande_code_filter_combo.addItem(code)

        self.ui.date_filter_combo.blockSignals(False)
        self.ui.commande_code_filter_combo.blockSignals(False)

        # Remplir le tableau
        for cmd in self.unvoiced_commandes:
            row = [
                QStandardItem(str(cmd['id'])),
                QStandardItem(cmd['code_commande']),
                QStandardItem(cmd['client_name']),
                QStandardItem(cmd['date_commande'].strftime('%Y-%m-%d')),
                QStandardItem(f"{cmd['total_ttc']:.2f}")
            ]
            self.model.appendRow(row)

        # self.ui.commandes_table_view.resizeColumnsToContents() # Removed in favor of Stretch

    def apply_filters(self):
        client_id = self.ui.client_filter_combo.currentData()
        date_str = self.ui.date_filter_combo.currentText() if self.ui.date_filter_combo.currentIndex() > 0 else None
        code = self.ui.commande_code_filter_combo.currentText() if self.ui.commande_code_filter_combo.currentIndex() > 0 else None

        for row in range(self.model.rowCount()):
            row_client_id = next((cmd['client_id'] for cmd in self.unvoiced_commandes if str(cmd['id']) == self.model.item(row, 0).text()), None)
            row_date_str = self.model.item(row, 3).text()
            row_code = self.model.item(row, 1).text()

            client_match = not client_id or row_client_id == client_id
            date_match = not date_str or row_date_str == date_str
            code_match = not code or row_code == code

            self.ui.commandes_table_view.setRowHidden(row, not (client_match and date_match and code_match))

    def on_selection_changed(self, selected, deselected):
        is_selection = self.ui.commandes_table_view.selectionModel().hasSelection()
        self.generate_button.setEnabled(is_selection)
        if is_selection:
            selected_rows = self.ui.commandes_table_view.selectionModel().selectedRows()
            if selected_rows:
                selected_row = selected_rows[0].row()
                # Remonter à la source du modèle si un proxy est utilisé
                source_index = self.proxy_model.mapToSource(self.proxy_model.index(selected_row, 0))
                self.selected_commande_id = self.model.item(source_index.row(), 0).text()
            else:
                 self.selected_commande_id = None
        else:
            self.selected_commande_id = None

    def get_selected_commande_id(self):
        return int(self.selected_commande_id) if self.selected_commande_id else None
