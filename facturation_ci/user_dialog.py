from PyQt6.QtWidgets import QDialog, QMessageBox
from page._user_dialog import Ui_UserDialog
from models.user import UserModel
from core.theme import STYLESHEET

class UserDialog(QDialog):
    def __init__(self, db_manager, user_data=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = user_data
        self.user_model = UserModel(self.db_manager)

        self.ui = Ui_UserDialog()
        self.ui.setupUi(self)
        self.setStyleSheet(STYLESHEET)

        self.load_roles()
        if self.user_data:
            self.load_data()
            self.setWindowTitle("Modifier l'utilisateur")
            # Password not required for edit
            self.ui.label_3.setText("Mot de passe (laisser vide pour ne pas changer) :")
        else:
            self.setWindowTitle("Nouveau Utilisateur")

    def load_roles(self):
        roles = self.user_model.get_roles()
        for role in roles:
            self.ui.role_combo.addItem(role['name'], role['id'])

    def load_data(self):
        self.ui.username_edit.setText(self.user_data['username'])
        self.ui.fullname_edit.setText(self.user_data['full_name'])

        # Select current role
        index = self.ui.role_combo.findData(self.user_data['role_id'])
        if index >= 0:
            self.ui.role_combo.setCurrentIndex(index)

        self.ui.active_check.setChecked(bool(self.user_data['is_active']))

    def get_data(self):
        role_id = self.ui.role_combo.currentData()
        data = {
            'username': self.ui.username_edit.text(),
            'full_name': self.ui.fullname_edit.text(),
            'password': self.ui.password_edit.text(),
            'role_id': role_id,
            'is_active': self.ui.active_check.isChecked()
        }
        return data

    def accept(self):
        data = self.get_data()

        if not data['username']:
            QMessageBox.warning(self, "Erreur", "Le nom d'utilisateur est requis.")
            return

        if not self.user_data and not data['password']:
            QMessageBox.warning(self, "Erreur", "Le mot de passe est requis pour un nouvel utilisateur.")
            return

        super().accept()
