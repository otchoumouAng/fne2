import os
import webbrowser
from PyQt6.QtWidgets import QWidget, QMessageBox, QHeaderView
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QThread

from page._avoir_list_page import Ui_AvoirListPage
from models.avoir import FactureAvoirModel
from models.company import CompanyInfoModel
from models.facture import FactureModel
from models.commande import CommandeModel
import core.fne_client as fne_client
from avoir_viewer_dialog import AvoirViewerDialog
from core.pdf_generator import PDFGenerator
from core.worker import Worker

class AvoirListPage(QWidget):
    def __init__(self, db_manager, main_window, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.main_window = main_window
        self.avoir_model = FactureAvoirModel(self.db_manager)
        self.company_model = CompanyInfoModel(self.db_manager)
        self.facture_model = FactureModel(self.db_manager)
        self.commande_model = CommandeModel(self.db_manager)
        self.thread = None
        self.worker = None
        self.is_task_running = False

        self.ui = Ui_AvoirListPage()
        self.ui.setupUi(self)

        self.setup_table()
        self.setup_connections()
        self.load_data()

    def setup_table(self):
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            'ID', 'Code Avoir', 'Date Création', 'Facture d\'Origine', 'Total TTC', 'Statut FNE'
        ])
        self.ui.table_view.setModel(self.table_model)
        self.ui.table_view.setColumnHidden(0, True)
        self.ui.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.ui.certify_button.setEnabled(False)
        self.ui.print_button.setEnabled(False)

    def setup_connections(self):
        self.ui.table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.ui.table_view.doubleClicked.connect(self.open_avoir_details)
        self.ui.print_button.clicked.connect(self.print_avoir)
        self.ui.certify_button.clicked.connect(self.certify_avoir)

    def certify_avoir(self):
        if self.is_task_running:
            QMessageBox.warning(self, "Tâche en cours", "Une autre tâche est déjà en cours. Veuillez patienter.")
            return

        avoir_id = self.get_selected_avoir_id()
        if not avoir_id:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner un avoir à certifier.")
            return

        avoir_data = self.avoir_model.get_by_id(avoir_id)
        if not avoir_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'avoir ID {avoir_id}.")
            return

        if avoir_data.get('statut_fne') == 'success':
            QMessageBox.information(self, "Déjà certifié", "Cet avoir a déjà été certifié avec succès.")
            return

        original_facture_id = avoir_data['facture_origine_id']
        fne_invoice_id = self.facture_model.get_fne_invoice_id(original_facture_id)
        if not fne_invoice_id:
            QMessageBox.warning(self, "Facture d'origine non certifiée", "La facture d'origine de cet avoir n'est pas encore certifiée par le FNE. Veuillez d'abord certifier la facture.")
            return

        commande_id = self.facture_model.get_commande_id_from_facture(original_facture_id)
        if not commande_id:
            QMessageBox.critical(self, "Erreur Critique", "Impossible de trouver la commande d'origine.")
            return
        original_items_with_fne_id = self.commande_model.get_items_with_fne_id(commande_id)

        fne_item_id_map = {item['id']: item['fne_item_id'] for item in original_items_with_fne_id}

        items_to_refund = []
        for item in avoir_data['lignes_avoir']:
            commande_item_id = item['commande_item_id']
            fne_item_id = fne_item_id_map.get(commande_item_id)
            if not fne_item_id:
                QMessageBox.critical(self, "Erreur de Données", f"L'article '{item['description']}' sur l'avoir n'a pas d'ID de certification FNE correspondant sur la facture d'origine.")
                return
            items_to_refund.append({
                "id": fne_item_id,
                "quantity": float(item['quantity'])
            })

        company_info = self.company_model.get_first()
        api_key = company_info.get('fne_api_key')
        if not api_key:
            QMessageBox.critical(self, "Erreur de configuration", "La clé d'API FNE pour l'entreprise n'est pas configurée.")
            return

        self.is_task_running = True
        self.thread = QThread()
        self.worker = Worker(
            fne_client.refund_invoice,
            api_key=api_key,
            original_fne_invoice_id=fne_invoice_id,
            items_to_refund=items_to_refund
        )
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(lambda result: self.on_avoir_certification_finished(avoir_id, result))
        self.worker.error.connect(lambda error_msg: self.on_avoir_certification_error(avoir_id, error_msg))
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.ui.certify_button.setEnabled(False)
        self.ui.print_button.setEnabled(False)
        self.main_window.statusBar().showMessage(f"Génération du PDF pour l'avoir {avoir_data['code_avoir']} en cours...")

    def on_avoir_certification_finished(self, avoir_id, fne_data):
        self.is_task_running = False
        nim = fne_data.get('nim')
        qr_code = fne_data.get('qr_code')
        fne_created_at = fne_data.get('fne_created_at')
        QMessageBox.information(self, "Succès", f"Avoir certifié avec succès.\nNIM: {nim}")

        self.avoir_model.update_fne_status(avoir_id, 'success', nim=nim, qr_code=qr_code, fne_created_at=fne_created_at)
        self.load_data()
        self.on_selection_changed(None, None)

    def on_avoir_certification_error(self, avoir_id, error_message):
        self.is_task_running = False
        QMessageBox.critical(self, "Erreur de Certification FNE", error_message)
        self.avoir_model.update_fne_status(avoir_id, 'failed', error_message=error_message)
        self.load_data()
        self.on_selection_changed(None, None)

    def load_data(self):
        avoirs = self.avoir_model.get_all()
        self.table_model.removeRows(0, self.table_model.rowCount())
        for avoir in avoirs:
            row = [
                QStandardItem(str(avoir['id'])),
                QStandardItem(avoir['code_avoir']),
                QStandardItem(avoir['date_creation'].strftime('%Y-%m-%d')),
                QStandardItem(avoir['code_facture_origine']),
                QStandardItem(f"{avoir['total_ttc']:.2f}"),
                QStandardItem(avoir['statut_fne'])
            ]
            self.table_model.appendRow(row)
        # self.ui.table_view.resizeColumnsToContents() # Removed to prefer Stretch mode
        self.on_selection_changed(None, None)

    def on_selection_changed(self, selected, deselected):
        has_selection = self.ui.table_view.selectionModel().hasSelection()
        self.ui.print_button.setEnabled(has_selection)
        self.ui.certify_button.setEnabled(has_selection)

    def get_selected_avoir_id(self):
        selected_indexes = self.ui.table_view.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        return int(self.table_model.item(selected_indexes[0].row(), 0).text())

    def open_avoir_details(self, index):
        avoir_id = self.get_selected_avoir_id()
        if avoir_id is None: return
        dialog = AvoirViewerDialog(self.db_manager, avoir_id=avoir_id, parent=self)
        dialog.exec()

    def print_avoir(self):
        if self.is_task_running:
            QMessageBox.warning(self, "Tâche en cours", "Une autre tâche est déjà en cours. Veuillez patienter.")
            return

        avoir_id = self.get_selected_avoir_id()
        if not avoir_id: return

        avoir_data = self.avoir_model.get_by_id(avoir_id)
        if not avoir_data:
            QMessageBox.critical(self, "Erreur", f"Impossible de charger l'avoir ID {avoir_id}.")
            return

        company_info = self.company_model.get_first()
        client_info = {
            "name": avoir_data.get('client_name', 'N/A'),
            "address": avoir_data.get('client_address', 'N/A'),
            "email": avoir_data.get('client_email', 'N/A'),
            "contact": avoir_data.get('client_contact', 'N/A')
        }

        generator = PDFGenerator(template_file="avoir.html")
        context = {
            "company": company_info,
            "client": client_info,
            "invoice": avoir_data,
            "details": avoir_data['lignes_avoir']
        }
        html_content = generator.render_html(**context)
        output_file = f"Avoir-{avoir_data['code_avoir']}.pdf"

        self.is_task_running = True
        self.thread = QThread()
        self.worker = Worker(generator.generate_pdf, html_content, output_file)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(lambda: self.on_printing_finished(output_file))
        self.worker.error.connect(self.on_printing_error)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()
        self.ui.certify_button.setEnabled(False)
        self.ui.print_button.setEnabled(False)

    def on_printing_finished(self, output_file):
        self.is_task_running = False
        self.on_selection_changed(None, None)
        self.main_window.statusBar().showMessage("Prêt", 3000)
        reply = QMessageBox.information(self, "Impression terminée",
            f"Le document a été exporté : {output_file}\n\nVoulez-vous l'ouvrir ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(os.path.abspath(output_file))

    def on_printing_error(self, error_message):
        self.is_task_running = False
        self.on_selection_changed(None, None)
        self.main_window.statusBar().showMessage("Erreur lors de l'impression", 5000)
        QMessageBox.critical(self, "Erreur d'impression", f"Une erreur est survenue:\n{error_message}")