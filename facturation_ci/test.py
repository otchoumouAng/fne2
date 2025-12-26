import sys
from PyQt6 import QtCore, QtGui, QtWidgets

class ModernLoginDialog(QtWidgets.QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Connexion")
        self.resize(450, 550)
        # On supprime la barre de titre système pour un look 100% custom (optionnel)
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)

        # --- STRUCTURE ---
        # Layout principal
        self.main_layout = QtWidgets.QVBoxLayout(self)
        
        # Le conteneur "Carte" (Le fond blanc arrondi)
        self.container = QtWidgets.QFrame()
        self.container.setObjectName("Container")
        self.main_layout.addWidget(self.container)
        
        # Layout interne de la carte
        self.ui_layout = QtWidgets.QVBoxLayout(self.container)
        self.ui_layout.setContentsMargins(40, 40, 40, 40)
        self.ui_layout.setSpacing(20)

        # 1. Header (Bouton fermer + Titre)
        self.close_btn = QtWidgets.QPushButton("×")
        self.close_btn.setObjectName("CloseButton")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.clicked.connect(self.reject)
        
        header_layout = QtWidgets.QHBoxLayout()
        header_layout.addStretch()
        header_layout.addWidget(self.close_btn)
        self.ui_layout.addLayout(header_layout)

        # 2. Titre & Branding
        self.title = QtWidgets.QLabel("Bienvenue")
        self.title.setObjectName("Title")
        self.title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        self.subtitle = QtWidgets.QLabel("Connectez-vous à votre espace")
        self.subtitle.setObjectName("Subtitle")
        self.subtitle.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        
        self.ui_layout.addWidget(self.title)
        self.ui_layout.addWidget(self.subtitle)
        self.ui_layout.addSpacing(20)

        # 3. Champs de saisie (Remplacement de ton QFormLayout rigide)
        self.username_input = QtWidgets.QLineEdit()
        self.username_input.setPlaceholderText("Nom d'utilisateur")
        self.username_input.setObjectName("Input")

        self.password_input = QtWidgets.QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.password_input.setObjectName("Input")

        self.ui_layout.addWidget(self.username_input)
        self.ui_layout.addWidget(self.password_input)
        self.ui_layout.addSpacing(10)

        # 4. Actions (Bouton Login stylisé)
        self.login_btn = QtWidgets.QPushButton("SE CONNECTER")
        self.login_btn.setObjectName("PrimaryButton")
        self.login_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.accept)

        self.forgot_lbl = QtWidgets.QLabel("Mot de passe oublié ?")
        self.forgot_lbl.setObjectName("Link")
        self.forgot_lbl.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.forgot_lbl.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)

        self.ui_layout.addWidget(self.login_btn)
        self.ui_layout.addWidget(self.forgot_lbl)
        self.ui_layout.addStretch()

        # --- STYLE (La Magie UI/UX) ---
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet("""
            /* Fond transparent pour l'ombre portée */
            QDialog { background: transparent; }
            
            /* La Carte Principale */
            #Container {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #E0E0E0;
            }

            /* Typographie */
            #Title {
                font-family: 'Segoe UI', sans-serif;
                font-size: 28px;
                font-weight: bold;
                color: #333333;
            }
            #Subtitle {
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
                color: #757575;
                margin-bottom: 10px;
            }

            /* Champs de saisie modernes */
            #Input {
                border: 2px solid #F0F0F0;
                border-radius: 10px;
                padding: 12px 15px;
                background-color: #FAFAFA;
                font-size: 14px;
                selection-background-color: #6C63FF;
            }
            #Input:focus {
                border: 2px solid #6C63FF; /* Couleur Accent */
                background-color: #FFFFFF;
            }

            /* Bouton Principal (Gradient & Shadow) */
            #PrimaryButton {
                background-color: #6C63FF;
                color: white;
                border-radius: 10px;
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }
            #PrimaryButton:hover {
                background-color: #5a52d5;
            }
            #PrimaryButton:pressed {
                background-color: #4841aa;
            }

            /* Liens et Boutons secondaires */
            #Link {
                color: #6C63FF;
                font-size: 12px;
                margin-top: 10px;
            }
            #Link:hover { text-decoration: underline; }

            #CloseButton {
                background: transparent;
                color: #AAA;
                font-size: 20px;
                border: none;
                font-weight: bold;
            }
            #CloseButton:hover { color: #FF5555; }
        """)

        # Ajout d'une ombre portée (Drop Shadow) pour la profondeur
        shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(5)
        shadow.setColor(QtGui.QColor(0, 0, 0, 50))
        self.container.setGraphicsEffect(shadow)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ModernLoginDialog()
    window.show()
    sys.exit(app.exec())