import sys
import getpass
from PyQt6.QtWidgets import QApplication, QMessageBox, QDialog

from core.db_manager import DBManager
from auth_dialog import AuthDialog
from main_window import MainWindow

# Import des nouveaux modules
from dashboard import DashboardModule
from client import ClientModule
from product import ProductModule
from invoice import InvoiceModule
from commande import CommandeModule
from settings import SettingsModule
from avoir_list_page import AvoirListPage

def main():
    """Point d'entrée principal de l'application refactorisée."""
    app = QApplication(sys.argv)

    # --- Connexion à la base de données ---
    try:
        db_manager = DBManager()
        # On force une première connexion pour vérifier que tout est OK avant de continuer.
        db_manager.get_connection()
    except ConnectionError as e:
        QMessageBox.critical(None, "Erreur de Base de Données",
                             f"{e}\n\nVérifiez vos identifiants et que le service MySQL est bien démarré.\n"
                             "L'application va se fermer.")
        sys.exit(1)

    # --- Processus d'authentification ---
    auth_dialog = AuthDialog(db_manager)
    if auth_dialog.exec() == QDialog.DialogCode.Accepted:
        user_data = auth_dialog.get_user_data()
        if not user_data:
            db_manager.close()
            sys.exit(0) # L'utilisateur a fermé la boîte de dialogue sans se connecter
    else:
        # L'utilisateur a annulé la connexion
        db_manager.close()
        sys.exit(0)

    # --- Lancement de l'interface principale ---
    main_window = MainWindow(user_data)

    # --- Initialisation des modules et insertion dans la MainWindow ---
    # Les index correspondent à l'ordre dans le QListWidget du .ui
    dashboard_module = DashboardModule(db_manager)
    main_window.set_module_widget(0, dashboard_module)

    commande_module = CommandeModule(db_manager, user_data, main_window)
    main_window.set_module_widget(1, commande_module)

    invoice_module = InvoiceModule(db_manager, user_data, main_window)
    main_window.set_module_widget(2, invoice_module)

    avoir_list_page = AvoirListPage(db_manager, main_window)
    main_window.set_module_widget(3, avoir_list_page)

    # Client and Product modules are now handled inside Settings,
    # but the MainWindow loop might still initialize them or expect them?
    # In main_window.py we hid index 4 and 5.
    # So we don't strictly need to inject them here for the main sidebar,
    # but if they were used for something else, we should check.
    # Given the recent refactor, clients and products are created inside SettingsModule.
    # However, to be safe and consistent with main_window logic (which might still try to load them if accessed via code),
    # we can leave placeholders or just not set them.
    # But wait, MainWindow.set_module_widget replaces the placeholder in stacked widget.
    # If we don't replace them, the original placeholders from .ui remain.
    # Since we hid the buttons, users can't reach index 4 and 5 via sidebar.
    # But we should pass user_data to SettingsModule if it needs it for its sub-modules (Users, Permissions).
    # Currently SettingsModule only takes db_manager.

    # We need to update SettingsModule to accept user_data to pass it down to Client/Product/Users modules.

    client_module = ClientModule(db_manager, user_data=user_data)
    main_window.set_module_widget(4, client_module)

    product_module = ProductModule(db_manager, user_data=user_data)
    main_window.set_module_widget(5, product_module)

    # Le module Rapports (index 6) n'est pas implémenté.
    settings_module = SettingsModule(db_manager, user_data=user_data)
    # Connecter le signal de changement de permissions pour rafraîchir l'interface globale
    settings_module.permissionsChanged.connect(main_window.refresh_permissions)
    main_window.set_module_widget(7, settings_module)

    main_window.show()

    # --- Démarrage de la boucle d'événements ---
    exit_code = app.exec()

    # --- Nettoyage avant de quitter ---
    db_manager.close()

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
