import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

from page._client import Ui_ClientPage
from models.client import ClientModel
from crud_dialog import CrudDialog

class ClientModule(QWidget):
    def __init__(self, db_manager, parent=None, user_data=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = user_data
        self.model = ClientModel(self.db_manager)

        self.ui = Ui_ClientPage()
        self.ui.setupUi(self)

        self.fields_config = [
            {'name': 'name', 'label': 'Nom', 'type': 'QLineEdit', 'required': True},
            {'name': 'address', 'label': 'Adresse', 'type': 'QTextEdit'},
            {'name': 'email', 'label': 'Email', 'type': 'QLineEdit'},
            {'name': 'phone', 'label': 'Téléphone', 'type': 'QLineEdit'},
        ]

        self.connect_signals()
        self.apply_permissions()
        self.load_clients()

    def connect_signals(self):
        self.ui.new_button.clicked.connect(self.open_new_client_dialog)
        self.ui.edit_button.clicked.connect(self.open_edit_client_dialog)
        self.ui.delete_button.clicked.connect(self.delete_client)
        self.ui.table_view.doubleClicked.connect(self.handle_client_double_click)

    def apply_permissions(self):
        if not self.user_data:
            return
        perms = self.user_data.get('permissions', [])

        if 'clients.create' not in perms:
            self.ui.new_button.setVisible(False)
        if 'clients.edit' not in perms:
            self.ui.edit_button.setVisible(False)
        if 'clients.delete' not in perms:
            self.ui.delete_button.setVisible(False)

        # If user cannot edit, disable double click editing
        if 'clients.edit' not in perms:
            self.ui.table_view.doubleClicked.disconnect(self.handle_client_double_click)

    def handle_client_double_click(self, index):
        """Ouvre le dialogue d'édition au double-clic."""
        self.open_edit_client_dialog()

    def load_clients(self):
        clients = self.model.get_all()
        self.set_clients_in_view(clients)

    def set_clients_in_view(self, clients):
        model = QStandardItemModel()
        model.setHorizontalHeaderLabels(['ID', 'Nom', 'Adresse', 'Email', 'Téléphone'])
        self.ui.table_view.setModel(model)

        for client in clients:
            row = [
                QStandardItem(str(client['id'])),
                QStandardItem(client['name']),
                QStandardItem(client['address']),
                QStandardItem(client['email']),
                QStandardItem(client['phone'])
            ]
            for item in row:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

            model.appendRow(row)

        self.ui.table_view.setColumnHidden(0, True)
        self.ui.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def get_selected_client_id(self):
        selected_indexes = self.ui.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        model = self.ui.table_view.model()
        id_index = model.index(selected_indexes[0].row(), 0)
        client_id = model.data(id_index)
        return int(client_id) if client_id else None

    def open_new_client_dialog(self):
        dialog = CrudDialog(
            mode='new',
            fields_config=self.fields_config,
            title="Nouveau Client",
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if not new_data.get('name'):
                QMessageBox.warning(self, "Champ Requis", "Le nom du client ne peut pas être vide.")
                return

            if self.model.create(new_data):
                QMessageBox.information(self, "Succès", "Client créé avec succès.")
                self.load_clients()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de créer le client.")

    def open_edit_client_dialog(self):
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner un client à modifier.")
            return

        client_data = self.model.get_by_id(client_id)
        if not client_data:
            QMessageBox.critical(self, "Erreur", "Client non trouvé.")
            return

        dialog = CrudDialog(
            mode='edit',
            fields_config=self.fields_config,
            title="Modifier le Client",
            data=client_data,
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_data()
            if not updated_data.get('name'):
                QMessageBox.warning(self, "Champ Requis", "Le nom du client ne peut pas être vide.")
                return
            if self.model.update(client_id, updated_data):
                QMessageBox.information(self, "Succès", "Client mis à jour avec succès.")
                self.load_clients()
            else:
                QMessageBox.critical(self, "Erreur", "Impossible de mettre à jour le client.")

    def delete_client(self):
        client_id = self.get_selected_client_id()
        if client_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner un client à supprimer.")
            return

        client_data = self.model.get_by_id(client_id)
        if not client_data:
             QMessageBox.critical(self, "Erreur", "Client non trouvé.")
             return

        reply = QMessageBox.question(
            self,
            "Confirmation de Suppression",
            f"Êtes-vous sûr de vouloir supprimer le client '{client_data['name']}' ?\n"
            "Cette action ne peut pas être annulée.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self.model.delete(client_id):
                QMessageBox.information(self, "Succès", "Client supprimé avec succès.")
                self.load_clients()
            else:
                QMessageBox.critical(self, "Erreur",
                                     "Impossible de supprimer le client. Il est probablement lié à des factures existantes.")
