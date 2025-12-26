from PyQt6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import QSize, Qt
from page._main_window import Ui_MainWindow
from core.theme import STYLESHEET, BG_SIDEBAR, TEXT_MAIN
from models.user import UserModel
from core.db_manager import DBManager
import os

class MainWindow(QMainWindow):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.user_data = user_data

        # Load permissions
        self.db_manager = DBManager()
        self.user_model = UserModel(self.db_manager)
        self.user_data['permissions'] = self.user_model.get_user_permissions(self.user_data['id'])

        # Initialisation UI de base
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # APPLICATION DU THEME "MIDNIGHT PROFESSIONAL"
        self.setStyleSheet(STYLESHEET)

        # Configuration de la navigation et du style
        self.setup_custom_ui()
        self.setup_navigation()

        self.setWindowTitle(f"Facturation - SOGICI | Connecté: {self.user_data['full_name']}")

    def setup_custom_ui(self):
        """Applique des modifications structurelles pour le nouveau design."""

        # 1. Personnalisation de la Sidebar (Menu)
        self.ui.nav_menu.setIconSize(QSize(24, 24))
        self.ui.nav_menu.setSpacing(8) # Espace entre les items

        # Ajout du Logo SOGICI en haut via un item spécial
        # On insert un item vide ou avec une icône spéciale en haut, ou on utilise setItemWidget

        # NOTE: On va essayer d'insérer un widget contenant le logo au-dessus du QListWidget
        # Pour cela, on doit manipuler le layout parent (self.ui.horizontalLayout)

        # Récupération du layout principal
        layout = self.ui.horizontalLayout

        # Création d'un conteneur pour la sidebar (Logo + Menu)
        sidebar_container = QWidget()
        sidebar_container.setFixedWidth(200) # Un peu plus large pour le confort
        sidebar_container.setStyleSheet(f"background-color: {BG_SIDEBAR};")

        sidebar_layout = QVBoxLayout(sidebar_container)
        sidebar_layout.setContentsMargins(0, 20, 0, 0)
        sidebar_layout.setSpacing(10)

        # Ajout du Logo
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # On cherche d'abord le logo officiel "entreprise_logo.png" qui semble être le vrai logo, ou "logo_sogici.png"
        base_img_path = os.path.join(os.path.dirname(__file__), "images")
        potential_logos = ["entreprise_logo.png", "logo_sogici.png", "logo.png"]

        logo_found = False
        for logo_file in potential_logos:
            logo_path = os.path.join(base_img_path, logo_file)
            if os.path.exists(logo_path):
                pixmap = QPixmap(logo_path)
                if not pixmap.isNull():
                    # Redimensionnement (max width 160)
                    pixmap = pixmap.scaledToWidth(140, Qt.TransformationMode.SmoothTransformation)
                    logo_label.setPixmap(pixmap)
                    logo_found = True
                    break

        if not logo_found:
            # Fallback text
            logo_label.setText("SOGICI")
            logo_label.setStyleSheet(f"color: {TEXT_MAIN}; font-weight: bold; font-size: 24px;")

        sidebar_layout.addWidget(logo_label)

        # On déplace le nav_menu existant dans notre nouveau conteneur
        # Attention: nav_menu est déjà ajouté au horizontalLayout par setupUi
        # On doit le retirer du layout parent et l'ajouter au nôtre

        # Qt ne permet pas facilement de "move" un widget entre layouts sans le reparenter
        # On va ruser: on supprime le widget nav_menu du layout principal et on l'ajoute au sidebar_layout
        layout.removeWidget(self.ui.nav_menu)
        sidebar_layout.addWidget(self.ui.nav_menu)

        # Ajout du spacer en bas si nécessaire, mais QListWidget prend la place

        # Insertion du conteneur sidebar à la place de l'ancien menu (index 0)
        layout.insertWidget(0, sidebar_container)

        # Mise à jour de la largeur du menu pour s'adapter au conteneur
        self.ui.nav_menu.setMaximumWidth(16777215) # Retirer la limite fixe du .ui

    def setup_navigation(self):
        """Connecte le menu et définit les icônes."""
        self.ui.nav_menu.currentRowChanged.connect(self.ui.stacked_widget.setCurrentIndex)
        self.ui.stacked_widget.currentChanged.connect(self.on_page_changed)

        # Définition des icônes pour chaque item (ordre défini dans le .ui)
        # 0: Dashboard, 1: Commandes, 2: Factures, 3: Avoirs, 4: Rapports, 5: Paramètres
        # Note: Clients et Produits ont été retirés de la liste principale car ils sont dans Paramètres > Master Data

        # Le QListWidget dans le .ui a toujours 8 items. Nous devons en cacher deux.
        # Les items sont indexés 0..7.
        # On garde: 0 (Dash), 1 (Cmd), 2 (Fact), 3 (Av), 6 (Rapports), 7 (Params)
        # On cache: 4 (Clients), 5 (Produits)

        self.ui.nav_menu.item(4).setHidden(True)
        self.ui.nav_menu.item(5).setHidden(True)

        icon_map = {
            0: "icon_dashboard.svg",
            1: "icon_commandes.svg",
            2: "icon_factures.svg",
            3: "icon_avoirs.svg",
            6: "icon_rapports.svg",
            7: "icon_settings.svg"
        }

        base_path = os.path.join(os.path.dirname(__file__), "images")

        for index, icon_name in icon_map.items():
            item = self.ui.nav_menu.item(index)
            if item:
                icon_path = os.path.join(base_path, icon_name)
                if os.path.exists(icon_path):
                    item.setIcon(QIcon(icon_path))

        self.apply_permissions()

        # Sélection par défaut
        self.ui.nav_menu.setCurrentRow(0)

    def apply_permissions(self):
        """Masque les éléments du menu selon les permissions de l'utilisateur."""
        perms = self.user_data.get('permissions', [])

        # Map item index to required permission
        menu_perms = {
            0: 'dashboard.view',
            1: 'commandes.view',
            2: 'invoices.view',
            3: 'invoices.view', # Avoirs
            6: 'reports.view',
            7: 'settings.view'
        }

        # On doit aussi ré-afficher les items si la permission est accordée
        for index, perm in menu_perms.items():
            item = self.ui.nav_menu.item(index)
            if item:
                if perm not in perms:
                    item.setHidden(True)
                else:
                    # Note: index 4 (Clients) and 5 (Products) are hidden by default logic, we should not unhide them here based on generic views.
                    # But they are not in menu_perms dict, so they are safe.
                    item.setHidden(False)

    def refresh_permissions(self):
        """Rafraîchit les permissions de l'utilisateur et met à jour l'interface."""
        # 1. Re-fetch permissions
        if self.user_data:
            self.user_data['permissions'] = self.user_model.get_user_permissions(self.user_data['id'])

        # 2. Update self (Sidebar)
        self.apply_permissions()

        # 3. Propagate to children modules
        # Loop through all widgets in stacked widget
        for i in range(self.ui.stacked_widget.count()):
            widget = self.ui.stacked_widget.widget(i)
            # Some widgets might be wrapper widgets (like in Settings sub-pages, but those share user_data ref if passed?)
            # Or they check permissions in apply_permissions method.
            if hasattr(widget, 'apply_permissions'):
                widget.apply_permissions()

            # Note: Modules like ClientModule use `self.user_data` reference.
            # Since `self.user_data` is a dict and we updated it in-place (assigned to key 'permissions'),
            # all modules holding reference to this dict will see the new list.
            # We just need to trigger the UI update method.

    def on_page_changed(self, index):
        """Appelé lorsque la page change dans le QStackedWidget."""
        current_widget = self.ui.stacked_widget.widget(index)
        if current_widget:
            # Essayer d'appeler une méthode de rafraîchissement standard
            if hasattr(current_widget, 'refresh'):
                current_widget.refresh()
            elif hasattr(current_widget, 'refresh_data'):
                 current_widget.refresh_data()
            elif hasattr(current_widget, 'load_data'):
                current_widget.load_data()
            elif hasattr(current_widget, 'load_invoices'):
                current_widget.load_invoices()
            elif hasattr(current_widget, 'load_commandes'):
                current_widget.load_commandes(filter_today=True)

    def set_module_widget(self, index, widget):
        """Remplace un widget placeholder dans le QStackedWidget par le vrai module."""
        old_widget = self.ui.stacked_widget.widget(index)
        self.ui.stacked_widget.removeWidget(old_widget)
        self.ui.stacked_widget.insertWidget(index, widget)
        old_widget.deleteLater()
