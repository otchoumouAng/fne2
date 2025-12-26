import sys
from PyQt6.QtWidgets import QWidget, QMessageBox, QDialog, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt

# Imports adaptés pour le module Commande
from page._commande import Ui_CommandePage
from models.commande import CommandeModel
from models.client import ClientModel
from commande_editor_dialog import CommandeEditorDialog

class CommandeModule(QWidget):
    def __init__(self, db_manager, user_data, main_window, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = user_data
        self.main_window = main_window
        self.model = CommandeModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)

        # Utiliser l'UI de Commande
        self.ui = Ui_CommandePage()
        self.ui.setupUi(self)

        self.connect_signals()
        self.apply_permissions()
        self.load_commandes(filter_today=True) # Filtre par défaut

    def apply_permissions(self):
        if not self.user_data:
            return
        perms = self.user_data.get('permissions', [])

        if 'commandes.create' not in perms:
            self.ui.new_button.setVisible(False)
        if 'commandes.edit' not in perms:
            self.ui.edit_button.setVisible(False)
        if 'commandes.delete' not in perms:
            self.ui.delete_button.setVisible(False)

        # If user cannot edit, disable double click editing behavior
        # But we still want read-only access?
        # The handle_commande_double_click opens in read_only=True by default logic if just viewing?
        # Actually handle_commande_double_click opens with read_only=True.
        # But open_edit_commande_dialog opens for editing.
        # If we want to allow viewing details even if no edit permission, we keep it but ensure save is disabled in dialog.
        # However, typically double click is for action.
        # Let's keep double click for read-only view, which is safe.
        pass

    def connect_signals(self):
        self.ui.new_button.clicked.connect(self.open_new_commande_dialog)
        self.ui.edit_button.clicked.connect(self.open_edit_commande_dialog)
        self.ui.delete_button.clicked.connect(self.delete_commande)
        self.ui.table_view.doubleClicked.connect(self.handle_commande_double_click)
        # Les boutons d'impression et de certification ont été retirés de l'UI

    def load_commandes(self, filter_today=False):
        commandes = self.model.get_all_with_client_info(filter_today=filter_today)
        self.set_commandes_in_view(commandes)

    def set_commandes_in_view(self, commandes):
        if self.ui.table_view.model():
            self.ui.table_view.model().clear()

        model = QStandardItemModel()
        header = ['ID', 'Code Commande', 'Client', 'Date Commande', 'Total TTC', 'Statut']
        model.setHorizontalHeaderLabels(header)
        self.ui.table_view.setModel(model)

        for cmd in commandes:
            row = [
                QStandardItem(str(cmd['id'])),
                QStandardItem(cmd['code_commande']),
                QStandardItem(cmd['client_name']),
                QStandardItem(cmd['date_commande'].strftime('%Y-%m-%d')),
                QStandardItem(f"{cmd['total_ttc']:.2f}"),
                QStandardItem(cmd['statut'])
            ]
            model.appendRow(row)

        self.ui.table_view.setColumnHidden(0, True) # Cacher l'ID
        self.ui.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def get_selected_commande_id(self):
        selected_indexes = self.ui.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        model = self.ui.table_view.model()
        id_index = model.index(selected_indexes[0].row(), 0)
        return int(model.data(id_index)) if model.data(id_index) else None

    def handle_commande_double_click(self, index):
        commande_id = self.get_selected_commande_id()
        if commande_id is None:
            return
        # Ouvre en mode lecture seule
        dialog = CommandeEditorDialog(self.db_manager, commande_id=commande_id, read_only=True)
        dialog.exec()

    def open_new_commande_dialog(self):
        dialog = CommandeEditorDialog(self.db_manager)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            commande_data = dialog.get_data()
            if commande_data:
                commande_data['details']['user_id'] = self.user_data['id']
                commande_id, error = self.model.create(commande_data)
                if error:
                    QMessageBox.critical(self, "Erreur", f"Impossible de créer la commande: {error}")
                else:
                    QMessageBox.information(self, "Succès", f"Commande ID {commande_id} créée avec succès.")
                    self.load_commandes(filter_today=True)

    def open_edit_commande_dialog(self):
        commande_id = self.get_selected_commande_id()
        if commande_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner une commande à modifier.")
            return

        # On peut potentiellement ajouter une logique pour empêcher la modification de commandes terminées/annulées
        commande_data = self.model.get_by_id(commande_id)
        if commande_data['details']['statut'] != 'en_cours':
            QMessageBox.warning(self, "Modification impossible", "Cette commande ne peut plus être modifiée car elle est terminée ou annulée.")
            return

        dialog = CommandeEditorDialog(self.db_manager, commande_id=commande_id)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_commande_data = dialog.get_data()
            if new_commande_data:
                success, error = self.model.update(commande_id, new_commande_data)
                if error:
                     QMessageBox.critical(self, "Erreur de mise à jour", f"Impossible de mettre à jour la commande: {error}")
                else:
                    QMessageBox.information(self, "Succès", "Commande mise à jour avec succès.")
                    self.load_commandes(filter_today=True)

    def delete_commande(self):
        commande_id = self.get_selected_commande_id()
        if commande_id is None:
            QMessageBox.warning(self, "Aucune Sélection", "Veuillez sélectionner une commande à supprimer.")
            return

        # Empêcher la suppression de commandes terminées
        commande_data = self.model.get_by_id(commande_id)
        if commande_data['details']['statut'] != 'en_cours':
            QMessageBox.warning(self, "Suppression impossible", "Cette commande ne peut pas être supprimée car elle est terminée ou annulée.")
            return

        reply = QMessageBox.question(self, 'Confirmation de suppression',
                                     f"Êtes-vous sûr de vouloir supprimer la commande ID {commande_id} ?\n"
                                     "Cette action est irréversible.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            success, error = self.model.delete(commande_id)
            if error:
                QMessageBox.critical(self, "Erreur de suppression", f"Impossible de supprimer la commande: {error}")
            else:
                QMessageBox.information(self, "Succès", "La commande a été supprimée avec succès.")
                self.load_commandes(filter_today=True)
