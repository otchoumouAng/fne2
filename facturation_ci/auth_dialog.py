from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6 import QtCore
import bcrypt
import os

from page._login import Ui_LoginDialog
from core.theme import STYLESHEET

class AuthDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = None

        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)
        self.setStyleSheet(STYLESHEET)

        # --- CORRECTION DE L'IMAGE DE FOND (MÉTHODE CSS ABSOLUE) ---
        # 1. On récupère le chemin absolu du fichier image
        image_path = os.path.join(os.getcwd(), "images", "bg-login.png")

        # 2. On vérifie si l'image existe
        if os.path.exists(image_path):
            # 3. IMPORTANT : On remplace les backslashes (\) par des slashes (/) 
            # car Qt CSS ne comprend pas les chemins Windows avec \
            unix_path = image_path.replace('\\', '/')
            
            # 4. On injecte le CSS directement avec le chemin complet
            # J'utilise 'border-image' au lieu de 'background-image' pour que l'image 
            # s'étire et remplisse tout le cadre (effet "cover")
            self.ui.LeftBox.setStyleSheet(f"""
                #LeftBox {{
                    border-image: url("{unix_path}") 0 0 0 0 stretch stretch;
                    border-top-left-radius: 10px;
                    border-bottom-left-radius: 10px;
                }}
            """)
            print(f"Image chargée depuis : {unix_path}") # Pour debug
        else:
            print(f"ERREUR : Image non trouvée à : {image_path}")
            # Fallback : une couleur si l'image n'est pas là
            self.ui.LeftBox.setStyleSheet("""
                #LeftBox {
                    background-color: #4e54c8;
                    border-top-left-radius: 10px;
                    border-bottom-left-radius: 10px;
                }
            """)
        # ------------------------------------------------------

        # Connexions
        self.ui.login_btn.clicked.connect(self.handle_login)
        self.ui.close_btn.clicked.connect(self.reject)

        # --- FENÊTRE SANS BORDURE ---
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        # ----------------------------

    # --- DÉPLACEMENT DE LA FENÊTRE ---
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.dragPosition = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCore.Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.dragPosition)
            event.accept()

    def handle_login(self):
        username = self.ui.username_input.text()
        password = self.ui.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Champs vides", "Veuillez entrer un nom d'utilisateur et un mot de passe.")
            return

        user_data = self._check_credentials(username, password)
        if user_data:
            self.user_data = user_data
            self.accept()
        else:
            QMessageBox.warning(self, "Échec de la connexion", "Nom d'utilisateur ou mot de passe incorrect.")

    def _check_credentials(self, username, password):
        """Vérifie les identifiants et récupère les permissions de l'utilisateur."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                u.id, u.username, u.password_hash, u.full_name, r.name as role,
                GROUP_CONCAT(p.name) as permissions
            FROM users u
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN role_permissions rp ON r.id = rp.role_id
            LEFT JOIN permissions p ON rp.permission_id = p.id
            WHERE u.username = %s AND u.is_active = TRUE
            GROUP BY u.id
        """
        try:
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                del user['password_hash']
                if user['permissions']:
                    user['permissions'] = set(user['permissions'].split(','))
                else:
                    user['permissions'] = set()
                return user
            return None
        except Exception as e:
            print(f"Erreur lors de la vérification des identifiants: {e}")
            return None
        finally:
            cursor.close()

    def get_user_data(self):
        """Retourne les données de l'utilisateur si la connexion a réussi."""
        return self.user_data