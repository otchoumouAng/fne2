from PyQt6.QtWidgets import QWidget, QListWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from page._permissions import Ui_PermissionsPage
from models.user import UserModel
from models.permission import PermissionModel

class PermissionsModule(QWidget):
    permissionsChanged = pyqtSignal()

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_model = UserModel(self.db_manager)
        self.perm_model = PermissionModel(self.db_manager)

        self.ui = Ui_PermissionsPage()
        self.ui.setupUi(self)

        self.load_roles()
        self.load_all_permissions()

        self.ui.roles_list.currentItemChanged.connect(self.on_role_selected)
        self.ui.save_button.clicked.connect(self.save_permissions)

    def load_roles(self):
        roles = self.user_model.get_roles()
        self.ui.roles_list.clear()
        for role in roles:
            item = QListWidgetItem(role['name'])
            item.setData(Qt.ItemDataRole.UserRole, role['id'])
            self.ui.roles_list.addItem(item)

    def load_all_permissions(self):
        perms = self.perm_model.get_all_permissions()
        self.ui.permissions_list.clear()
        for perm in perms:
            item = QListWidgetItem(perm['name'])
            item.setData(Qt.ItemDataRole.UserRole, perm['id'])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.ui.permissions_list.addItem(item)

    def on_role_selected(self, current, previous):
        if not current:
            return

        role_id = current.data(Qt.ItemDataRole.UserRole)
        role_perms = self.perm_model.get_role_permissions(role_id)

        for i in range(self.ui.permissions_list.count()):
            item = self.ui.permissions_list.item(i)
            perm_id = item.data(Qt.ItemDataRole.UserRole)
            if perm_id in role_perms:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)

    def save_permissions(self):
        current_role_item = self.ui.roles_list.currentItem()
        if not current_role_item:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner un rôle.")
            return

        role_id = current_role_item.data(Qt.ItemDataRole.UserRole)
        selected_perms = []

        for i in range(self.ui.permissions_list.count()):
            item = self.ui.permissions_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_perms.append(item.data(Qt.ItemDataRole.UserRole))

        success, msg = self.perm_model.update_role_permissions(role_id, selected_perms)
        if success:
            QMessageBox.information(self, "Succès", "Permissions mises à jour.")
            self.permissionsChanged.emit()
        else:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la mise à jour: {msg}")
