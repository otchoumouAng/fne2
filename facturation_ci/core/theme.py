from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QWidget
from PyQt6.QtGui import QColor

# --- PALETTE DE COULEURS "INDIGO CORPORATE" ---

# Fonds
BG_APP = "#f1f5f9"       # Slate 100 - Gris bleuté très pâle (Standard SaaS moderne)
BG_CARD = "#ffffff"      # Blanc pur
BG_SIDEBAR = "#ffffff"   # Blanc

# COULEUR PRINCIPALE : ROYAL INDIGO
# Une couleur profonde, sérieuse et élégante.
PRIMARY = "#4f46e5"      # Indigo 600
PRIMARY_HOVER = "#4338ca" # Indigo 700
PRIMARY_PRESSED = "#3730a3" # Indigo 800
PRIMARY_TEXT = "#ffffff"

# Dégradé subtil pour les boutons (Indigo vers Violet léger)
# Cela donne un aspect "premium" et moins plat.
PRIMARY_GRADIENT = "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4f46e5, stop:1 #6366f1)"

# Textes
TEXT_MAIN = "#0f172a"    # Slate 900 (Noir profond, très lisible)
TEXT_SEC = "#64748b"     # Slate 500 (Gris équilibré)
TEXT_TER = "#94a3b8"     # Slate 400

# Utilitaires
BORDER = "#e2e8f0"       # Slate 200 (Bordure très fine)
BORDER_FOCUS = "#6366f1" # Focus Indigo clair
SELECTION_BG = "rgba(79, 70, 229, 0.08)" # Fond Indigo très très léger (8%)
SUCCESS = "#10b981"      # Emerald 500
DANGER = "#ef4444"       # Red 500
WARNING = "#f59e0b"      # Amber 500

STYLESHEET = f"""
/* --- GLOBAL RESET --- */
QWidget {{
    font-family: 'Inter', 'Segoe UI', 'Roboto', sans-serif; /* J'ai ajouté Inter en premier, si dispo */
    font-size: 14px;
    color: {TEXT_MAIN};
}}

QMainWindow, QDialog {{
    background-color: {BG_APP};
}}

/* --- SIDEBAR (Navigation Pro) --- */
QListWidget#nav_menu {{
    background-color: {BG_SIDEBAR};
    border: none;
    border-right: 1px solid {BORDER};
    outline: none;
    padding-top: 20px;
}}
QListWidget#nav_menu::item {{
    background-color: transparent;
    color: {TEXT_SEC};
    height: 45px;
    padding-left: 20px;
    margin: 4px 15px; /* Marges latérales augmentées pour effet "capsule" */
    border-radius: 10px; /* Plus arrondi = plus moderne */
    border: 1px solid transparent;
}}
QListWidget#nav_menu::item:hover {{
    background-color: #f8fafc;
    color: {TEXT_MAIN};
}}
QListWidget#nav_menu::item:selected {{
    background-color: {SELECTION_BG};
    color: {PRIMARY};
    font-weight: 600;
    /* On change le style : pas de bordure gauche, mais tout le fond coloré léger */
}}

/* --- CONTENT AREA --- */
QStackedWidget {{
    background-color: {BG_APP};
    border: none;
}}

/* --- CARDS & PANELS --- */
QGroupBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
    margin-top: 20px;
    padding-top: 10px;
    font-weight: 600;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 20px;
    color: {TEXT_MAIN};
    font-size: 15px; /* Un peu plus petit et raffiné */
    letter-spacing: 0.5px;
    background-color: transparent; 
}}

/* Helper pour QFrame style carte */
QFrame[class="card"] {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

/* --- BUTTONS: HERO (Primary) --- */
QPushButton {{
    background-color: {PRIMARY};
    background-color: {PRIMARY_GRADIENT};
    color: {PRIMARY_TEXT};
    border: 1px solid transparent;
    border-radius: 8px; /* Arrondi intermédiaire */
    padding: 10px 24px;
    font-weight: 600;
    font-size: 13px; /* Texte un peu plus petit = plus élégant */
    letter-spacing: 0.3px;
}}
QPushButton:hover {{
    background-color: {PRIMARY_HOVER};
    border: 1px solid rgba(255,255,255,0.1);
}}
QPushButton:pressed {{
    background-color: {PRIMARY_PRESSED};
    padding-top: 12px;
    padding-bottom: 8px;
}}
QPushButton:disabled {{
    background-color: {BG_APP};
    color: {TEXT_TER};
    border: 1px solid {BORDER};
}}

/* Boutons Secondaires (Outline) */
QPushButton[class="secondary"] {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    color: {TEXT_SEC};
}}
QPushButton[class="secondary"]:hover {{
    border-color: {TEXT_TER};
    color: {TEXT_MAIN};
    background-color: #f8fafc;
}}

/* --- QTOOLBUTTON (Soft Actions) --- */
QToolButton {{
    background-color: white;
    color: {TEXT_SEC};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 6px;
    font-weight: 500;
}}
QToolButton:hover {{
    background-color: {BG_APP}; /* Reste gris clair, très soft */
    color: {PRIMARY};         /* Seul le texte/icone devient Indigo */
    border: 1px solid {PRIMARY};
}}
QToolButton:pressed {{
    background-color: {SELECTION_BG};
}}

/* Menu Flèche */
QToolButton[popupMode="1"] {{
    padding-right: 25px;
}}
QToolButton::menu-button {{
    border: none;
    border-left: 1px solid {BORDER};
    width: 20px;
    border-top-right-radius: 8px;
    border-bottom-right-radius: 8px;
}}

/* --- INPUTS --- */
QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 9px 12px; /* Un peu plus de hauteur */
    color: {TEXT_MAIN};
}}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
    border: 1px solid {BORDER_FOCUS};
    background-color: {BG_CARD};
}}

/* --- TABLES (Clean Business Style) --- */
QTableWidget, QTableView {{
    background-color: {BG_CARD};
    gridline-color: {BG_APP}; /* Grille très subtile de la couleur du fond */
    border: 1px solid {BORDER};
    border-radius: 8px;
    outline: 0;
}}

QHeaderView::section {{
    background-color: #f8fafc; /* Gris très très clair */
    color: {TEXT_SEC};
    padding: 6px 5px;
    border: none;
    border-bottom: 1px solid {BORDER};
    font-weight: 600;
    text-transform: uppercase;
    font-size: 11px; /* En-tête discret */
    letter-spacing: 1px;
}}

QTableWidget::item, QTableView::item {{
    padding: 10px; /* Cellules aérées */
    border-bottom: 1px solid {BG_APP};
    color: {TEXT_MAIN};
    outline: none;
}}

QTableWidget::item:selected, QTableView::item:selected {{
    background-color: {SELECTION_BG};
    color: {PRIMARY};
    border: none;
}}

QTableWidget::item:focus, QTableView::item:focus {{
    outline: none;
    background-color: {SELECTION_BG};
}}

/* --- SCROLLBARS --- */
QScrollBar:vertical {{
    border: none;
    background: transparent;
    width: 6px; /* Plus fin */
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    min-height: 30px;
    border-radius: 3px;
}}
QScrollBar::handle:vertical:hover {{ background: {TEXT_SEC}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

/* --- MENUS --- */
QMenu {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER};
    padding: 6px;
    border-radius: 10px;
}}
QMenu::item {{
    padding: 8px 24px;
    color: {TEXT_MAIN};
    border-radius: 6px;
}}
QMenu::item:selected {{
    background-color: {SELECTION_BG}; /* Pas de fond bleu foncé, on reste soft */
    color: {PRIMARY};
}}

/* --- TYPOGRAPHY SPECIFIC --- */
QLabel[class="page-title"] {{
    font-size: 26px;
    font-weight: 700;
    color: {TEXT_MAIN};
    padding-bottom: 15px;
    border-bottom: 1px solid {BORDER};
    margin-bottom: 25px;
    letter-spacing: -0.5px; /* Kerning moderne */
}}

QLabel[class="kpi-value"] {{
    font-size: 38px;
    font-weight: 800;
    color: {PRIMARY};
    letter-spacing: -1px;
}}

QLabel[class="kpi-label"] {{
    font-size: 12px;
    color: {TEXT_SEC};
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}}
"""

# --- HELPER SHADOW ---
def apply_shadow(widget: QWidget, blur=20, x=0, y=4, alpha=10):
    """
    Ombre portée encore plus douce pour le thème 'Indigo'.
    Note l'alpha par défaut réduit à 10 (très subtil).
    """
    if widget is None:
        return
        
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setXOffset(x)
    shadow.setYOffset(y)
    # Ombre légèrement bleutée au lieu de noire pure pour un effet 'verre'
    shadow.setColor(QColor(30, 41, 59, alpha)) 
    widget.setGraphicsEffect(shadow)