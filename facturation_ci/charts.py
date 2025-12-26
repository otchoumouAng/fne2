import matplotlib
matplotlib.use('QtAgg') # Ensure we use the Qt backend

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from core.theme import BG_CARD, TEXT_MAIN, TEXT_SEC, PRIMARY, SUCCESS, DANGER, BORDER, BG_SIDEBAR

class BaseMatplotlibChart(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Container style to match the theme
        self.setStyleSheet(f"background-color: {BG_CARD}; border-radius: 12px; border: 1px solid {BORDER};")
        self.setMinimumHeight(300)

        # Add title label
        if title:
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet(f"color: {TEXT_MAIN}; font-weight: bold; font-size: 16px; border: none; background: transparent; padding: 10px;")
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            self.layout.addWidget(self.title_label)

        # Create Matplotlib Figure
        self.figure = Figure(figsize=(5, 4), dpi=100)
        # Set figure background to match theme card background
        self.figure.patch.set_facecolor(BG_CARD)

        self.canvas = FigureCanvas(self.figure)
        # Canvas widget needs transparent background to blend in if needed, but figure bg handles it
        self.canvas.setStyleSheet("background-color: transparent; border: none; border-radius: 0px;")

        self.layout.addWidget(self.canvas)

    def _setup_axes(self, ax):
        """Helper to style axes matching the theme."""
        ax.set_facecolor(BG_CARD)

        # Spine colors
        for spine in ax.spines.values():
            spine.set_color(BORDER)

        # Tick colors
        ax.tick_params(axis='x', colors=TEXT_SEC)
        ax.tick_params(axis='y', colors=TEXT_SEC)

        # Label colors
        ax.xaxis.label.set_color(TEXT_SEC)
        ax.yaxis.label.set_color(TEXT_SEC)

        # Title color if used
        ax.title.set_color(TEXT_MAIN)

class RevenueBarChart(BaseMatplotlibChart):
    def __init__(self, parent=None):
        super().__init__("Chiffre d'Affaires (6 derniers mois)", parent)
        self.ax = self.figure.add_subplot(111)
        self._setup_axes(self.ax)
        # Adjust layout to make room for labels
        self.figure.subplots_adjust(bottom=0.15, left=0.15, right=0.95, top=0.9)

    def update_data(self, data):
        """
        data: list of tuples (month_name, revenue_amount)
        """
        self.ax.clear()
        self._setup_axes(self.ax)

        if not data:
            self.canvas.draw()
            return

        months = [x[0] for x in data]
        revenues = [x[1] for x in data]

        # Create bars
        bars = self.ax.bar(months, revenues, color=PRIMARY, width=0.6)

        # Add value labels on top of bars
        for bar in bars:
            height = bar.get_height()
            display_val = f"{height/1000:.0f}k" if height >= 1000 else f"{height:.0f}"
            self.ax.text(bar.get_x() + bar.get_width()/2., height,
                         display_val,
                         ha='center', va='bottom', color=TEXT_MAIN, fontsize=9)

        # Remove top and right spines for cleaner look
        self.ax.spines['top'].set_visible(False)
        self.ax.spines['right'].set_visible(False)

        self.canvas.draw()

class StatusPieChart(BaseMatplotlibChart):
    def __init__(self, parent=None):
        super().__init__("Répartition des Factures", parent)
        self.ax = self.figure.add_subplot(111)
        self.figure.subplots_adjust(bottom=0.05, top=0.95, left=0.05, right=0.95)

    def update_data(self, status_counts):
        """
        status_counts: dict {'paid': 10, 'draft': 5, ...}
        """
        self.ax.clear()

        total = sum(status_counts.values())
        if total == 0:
            self.canvas.draw()
            return

        labels_map = {
            'paid': 'Payées',
            'certified': 'Certifiées',
            'draft': 'Brouillons',
            'cancelled': 'Annulées'
        }

        colors_map = {
            'paid': SUCCESS,
            'certified': PRIMARY,
            'draft': TEXT_SEC,
            'cancelled': DANGER
        }

        # Filter out zero values
        labels = []
        sizes = []
        colors = []

        for status, count in status_counts.items():
            if count > 0:
                labels.append(labels_map.get(status, status))
                sizes.append(count)
                colors.append(colors_map.get(status, "#aaaaaa"))

        # Donut chart
        wedges, texts, autotexts = self.ax.pie(
            sizes,
            labels=labels,
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            pctdistance=0.85,
            textprops=dict(color=TEXT_MAIN)
        )

        # Draw circle for donut hole
        centre_circle = matplotlib.patches.Circle((0,0), 0.60, fc=BG_CARD)
        self.ax.add_artist(centre_circle)

        self.ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Style text
        for text in texts:
            text.set_color(TEXT_MAIN)
            text.set_fontsize(9)
        for autotext in autotexts:
            autotext.set_color("white") # Percentages inside colored wedges? No, inside donut usually.
            # If donut, pctdistance 0.85 is inside the wedge. White text on colored wedge is good.
            # But wait, TEXT_SEC for draft is grey. White might be hard.
            autotext.set_fontsize(8)

        self.canvas.draw()
