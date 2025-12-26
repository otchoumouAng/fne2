from PyQt6.QtWidgets import (
    QWidget, QStackedWidget, QVBoxLayout, QGridLayout, QLabel, QPushButton,
    QHBoxLayout, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon

from page._settings import Ui_SettingsPage
from models.company import CompanyInfoModel
from settings_card import SettingsCard
from core.theme import TEXT_MAIN, BG_CARD
from client import ClientModule
from product import ProductModule
from users import UsersModule
from permissions import PermissionsModule

# --- 1. The Menu (Dashboard of Cards) ---
class SettingsMenuWidget(QWidget):
    def __init__(self, navigation_callback, parent=None):
        super().__init__(parent)
        self.navigation_callback = navigation_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("Paramètres Généraux")
        title.setProperty("class", "page-title")
        title.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        # Grid of Cards
        grid = QGridLayout()
        grid.setSpacing(20)
        layout.addLayout(grid)

        # Definition of cards
        # Definition of cards
        # Indices must match the order in SettingsModule constructor
        cards_data = [
            ("Paramétrages", "Préférences de l'application et options générales.", 2),
            ("Configuration", "Informations de l'entreprise, fiscales et bancaires.", 1),
            ("Master Data", "Gestion des données de référence (Produits, Clients, etc.)", 3),
            ("Utilisateurs", "Création et gestion des comptes utilisateurs.", 4),
            ("Permissions", "Attribution des rôles et droits d'accès.", 5)
        ]

        row, col = 0, 0
        for title_text, desc, index in cards_data:
            card = SettingsCard(title_text, desc)
            # Use a lambda that captures the current index correctly
            card.clicked.connect(lambda idx=index: self.navigation_callback(idx))
            grid.addWidget(card, row, col)

            col += 1
            if col > 1: # 2 cards per row
                col = 0
                row += 1

        # Spacer at bottom
        layout.addStretch()

# --- 2. The Existing Configuration Form (Wrapped) ---
class CompanyConfigWidget(QWidget):
    def __init__(self, db_manager, back_callback, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.back_callback = back_callback
        self.company_model = CompanyInfoModel(self.db_manager)

        self.ui = Ui_SettingsPage()
        self.ui.setupUi(self)

        # Add Back Button at the top
        self.setup_header()

        self.load_company_info()
        self.setup_connections()

    def setup_header(self):
        # We need to insert a header layout into the existing verticalLayout of Ui_SettingsPage
        # The existing layout is self.ui.verticalLayout

        header_layout = QHBoxLayout()
        back_btn = QPushButton("← Retour")
        back_btn.setObjectName("secondary") # Use theme style if defined, or just default
        back_btn.clicked.connect(self.back_callback)
        back_btn.setFixedWidth(100)

        title = QLabel("Configuration Entreprise")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT_MAIN};")

        header_layout.addWidget(back_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Insert at top (index 0)
        self.ui.verticalLayout.insertLayout(0, header_layout)

    def setup_connections(self):
        self.ui.save_button.clicked.connect(self.save_company_info)

    def load_company_info(self):
        company_info = self.company_model.get_first()
        if company_info:
            self.ui.name_edit.setText(company_info.get('name', ''))
            self.ui.address_edit.setPlainText(company_info.get('address', ''))
            self.ui.phone_edit.setText(company_info.get('phone', ''))
            self.ui.email_edit.setText(company_info.get('email', ''))
            self.ui.tax_id_edit.setText(company_info.get('ncc', ''))
            self.ui.pos_edit.setText(company_info.get('point_of_sale', ''))
            self.ui.fne_api_key_edit.setText(company_info.get('fne_api_key', ''))
            self.ui.tax_regime_edit.setText(company_info.get('tax_regime', ''))
            self.ui.tax_office_edit.setText(company_info.get('tax_office', ''))
            self.ui.rccm_edit.setText(company_info.get('rccm', ''))
            self.ui.bank_details_edit.setText(company_info.get('bank_details', ''))
            self.ui.establishment_edit.setText(company_info.get('establishment', ''))

    def get_form_data(self):
        return {
            'name': self.ui.name_edit.text(),
            'address': self.ui.address_edit.toPlainText(),
            'phone': self.ui.phone_edit.text(),
            'email': self.ui.email_edit.text(),
            'ncc': self.ui.tax_id_edit.text(),
            'point_of_sale': self.ui.pos_edit.text(),
            'fne_api_key': self.ui.fne_api_key_edit.text(),
            'tax_regime': self.ui.tax_regime_edit.text(),
            'tax_office': self.ui.tax_office_edit.text(),
            'rccm': self.ui.rccm_edit.text(),
            'bank_details': self.ui.bank_details_edit.text(),
            'establishment': self.ui.establishment_edit.text()
        }

    def save_company_info(self):
        data = self.get_form_data()
        if not data['name'] or not data['fne_api_key']:
            # Import QMessageBox here to avoid circular imports or just use parent
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Champs requis", "Le nom de l'entreprise et la clé d'API FNE sont requis.")
            return

        success, message = self.company_model.update_or_create(data)
        from PyQt6.QtWidgets import QMessageBox
        if success:
            QMessageBox.information(self, "Succès", "Les informations de l'entreprise ont été enregistrées avec succès.")
        else:
            QMessageBox.critical(self, "Erreur de Sauvegarde", f"Impossible d'enregistrer les informations : {message}")

# --- 3. Master Data Menu ---
class MasterDataMenuWidget(QWidget):
    def __init__(self, navigation_callback, back_callback, parent=None):
        super().__init__(parent)
        self.navigation_callback = navigation_callback
        self.back_callback = back_callback
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        back_btn = QPushButton("← Retour")
        back_btn.clicked.connect(self.back_callback)
        back_btn.setFixedWidth(100)

        title = QLabel("Gestion des Master Data")
        title.setStyleSheet(f"color: {TEXT_MAIN}; font-size: 24px; font-weight: bold;")

        header_layout.addWidget(back_btn)
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Grid of Cards
        grid = QGridLayout()
        grid.setSpacing(20)
        layout.addLayout(grid)

        # Definition of cards
        # Indices: 6=Clients, 7=Products
        cards_data = [
            ("Clients", "Gérer la liste des clients et leurs informations.", 6),
            ("Produits", "Gérer le catalogue des produits et services.", 7)
        ]

        row, col = 0, 0
        for title_text, desc, index in cards_data:
            card = SettingsCard(title_text, desc)
            card.clicked.connect(lambda idx=index: self.navigation_callback(idx))
            grid.addWidget(card, row, col)

            col += 1
            if col > 1:
                col = 0
                row += 1

        layout.addStretch()

# --- 4. Wrappers for Client and Product Modules to add Back button ---
class ClientConfigWidget(QWidget):
    def __init__(self, db_manager, back_callback, user_data=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 0)
        back_btn = QPushButton("← Retour Master Data")
        back_btn.clicked.connect(back_callback)
        back_btn.setFixedWidth(150)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Content
        self.client_module = ClientModule(db_manager, user_data=user_data)
        layout.addWidget(self.client_module)

class ProductConfigWidget(QWidget):
    def __init__(self, db_manager, back_callback, user_data=None, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 0)
        back_btn = QPushButton("← Retour Master Data")
        back_btn.clicked.connect(back_callback)
        back_btn.setFixedWidth(150)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Content
        self.product_module = ProductModule(db_manager, user_data=user_data)
        layout.addWidget(self.product_module)

# --- Wrapper for Users Module ---
class UsersConfigWidget(QWidget):
    def __init__(self, db_manager, back_callback, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 0)
        back_btn = QPushButton("← Retour Paramètres")
        back_btn.clicked.connect(back_callback)
        back_btn.setFixedWidth(150)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.users_module = UsersModule(db_manager)
        layout.addWidget(self.users_module)

# --- Wrapper for Permissions Module ---
class PermissionsConfigWidget(QWidget):
    permissionsChanged = pyqtSignal()

    def __init__(self, db_manager, back_callback, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 0)
        back_btn = QPushButton("← Retour Paramètres")
        back_btn.clicked.connect(back_callback)
        back_btn.setFixedWidth(150)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.perms_module = PermissionsModule(db_manager)
        self.perms_module.permissionsChanged.connect(self.permissionsChanged.emit)
        layout.addWidget(self.perms_module)

# --- 5. Placeholder Widget for Under Construction Pages ---
class PlaceholderWidget(QWidget):
    def __init__(self, title, back_callback, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        # Header
        header_layout = QHBoxLayout()
        back_btn = QPushButton("← Retour")
        back_btn.clicked.connect(back_callback)
        back_btn.setFixedWidth(100)
        page_title = QLabel(title)
        page_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {TEXT_MAIN};")
        header_layout.addWidget(back_btn)
        header_layout.addWidget(page_title)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Content
        content = QLabel("Cette fonctionnalité est en cours de développement.")
        content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content.setStyleSheet("font-size: 16px; color: #7f8c8d; margin-top: 50px;")
        layout.addWidget(content)
        layout.addStretch()

# --- 6. Main Settings Module (Controller) ---
class SettingsModule(QStackedWidget):
    permissionsChanged = pyqtSignal()

    def __init__(self, db_manager, user_data=None, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = user_data

        # Page 0: Menu
        self.menu_page = SettingsMenuWidget(self.navigate_to)
        self.addWidget(self.menu_page)

        # Page 1: Configuration (Company Info)
        self.config_page = CompanyConfigWidget(self.db_manager, self.go_back)
        self.addWidget(self.config_page)

        # Page 2: Paramétrages
        self.addWidget(PlaceholderWidget("Paramétrages", self.go_back))

        # Page 3: Master Data (Dashboard)
        self.master_data_page = MasterDataMenuWidget(self.navigate_to_master_data, self.go_back)
        self.addWidget(self.master_data_page)

        # Page 4: Utilisateurs
        self.users_page = UsersConfigWidget(self.db_manager, self.go_back)
        self.addWidget(self.users_page)

        # Page 5: Permissions
        self.permissions_page = PermissionsConfigWidget(self.db_manager, self.go_back)
        self.permissions_page.permissionsChanged.connect(self.permissionsChanged.emit)
        self.addWidget(self.permissions_page)

        # Sub-pages for Master Data (hidden from main flow, accessed via master_data_page)
        # 6: Client Management
        self.client_page = ClientConfigWidget(self.db_manager, self.go_to_master_data_menu, user_data=self.user_data)
        self.addWidget(self.client_page)

        # 7: Product Management
        self.product_page = ProductConfigWidget(self.db_manager, self.go_to_master_data_menu, user_data=self.user_data)
        self.addWidget(self.product_page)

        self.setCurrentIndex(0)

    def navigate_to(self, index):
        self.setCurrentIndex(index)

    def go_back(self):
        self.setCurrentIndex(0)

    def navigate_to_master_data(self, index):
        self.setCurrentIndex(index)

    def go_to_master_data_menu(self):
        self.setCurrentIndex(3) # Index of MasterDataMenuWidget
