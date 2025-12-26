from PyQt6.QtWidgets import QWidget, QMessageBox, QHeaderView, QDialog
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from page._users import Ui_UsersPage
from models.user import UserModel
from user_dialog import UserDialog

class UsersModule(QWidget):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.model = UserModel(self.db_manager)

        self.ui = Ui_UsersPage()
        self.ui.setupUi(self)

        self.setup_table()
        self.connect_signals()
        self.load_users()

    def setup_table(self):
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(['ID', 'Utilisateur', 'Nom Complet', 'Rôle', 'Actif'])
        self.ui.table_view.setModel(self.table_model)
        self.ui.table_view.setColumnHidden(0, True)
        self.ui.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def connect_signals(self):
        self.ui.new_button.clicked.connect(self.open_new_user_dialog)
        self.ui.edit_button.clicked.connect(self.open_edit_user_dialog)
        self.ui.delete_button.clicked.connect(self.delete_user)
        self.ui.table_view.doubleClicked.connect(self.open_edit_user_dialog)

    def load_users(self):
        users = self.model.get_all()
        self.table_model.removeRows(0, self.table_model.rowCount())

        for user in users:
            row = [
                QStandardItem(str(user['id'])),
                QStandardItem(user['username']),
                QStandardItem(user['full_name'] or ""),
                QStandardItem(user['role_name']),
                QStandardItem("Oui" if user['is_active'] else "Non")
            ]
            self.table_model.appendRow(row)

    def get_selected_user_id(self):
        selected = self.ui.table_view.selectionModel().selectedRows()
        if not selected:
            return None
        return int(self.table_model.item(selected[0].row(), 0).text())

    def open_new_user_dialog(self):
        dialog = UserDialog(self.db_manager, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            success, msg = self.model.create(data)
            if success:
                QMessageBox.information(self, "Succès", "Utilisateur créé.")
                self.load_users()
            else:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la création: {msg}")

    def open_edit_user_dialog(self):
        user_id = self.get_selected_user_id()
        if not user_id:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un utilisateur.")
            return

        user = self.model.get_by_id(user_id)
        if not user:
            QMessageBox.critical(self, "Erreur", "Utilisateur introuvable.")
            return

        dialog = UserDialog(self.db_manager, user_data=user, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            success, msg = self.model.update(user_id, data)
            if success:
                QMessageBox.information(self, "Succès", "Utilisateur mis à jour.")
                self.load_users()
            else:
                QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour: {msg}")

    def delete_user(self):
        user_id = self.get_selected_user_id()
        if not user_id:
            return

        if QMessageBox.question(self, "Confirmation", "Supprimer cet utilisateur ?",
                              QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            success, msg = self.model.delete(user_id)
            if success:
                self.load_users()
            else:
                QMessageBox.critical(self, "Erreur", f"Impossible de supprimer: {msg}")
