import os
import webbrowser
from PyQt6.QtWidgets import QDialog, QMessageBox
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QThread

from page._credit_note_list_dialog import Ui_CreditNoteListDialog
from models.avoir import FactureAvoirModel
from models.company import CompanyInfoModel
from models.client import ClientModel
from models.facture import FactureModel
from models.commande import CommandeModel
import core.fne_client as fne_client
from avoir_viewer_dialog import AvoirViewerDialog
from core.pdf_generator import PDFGenerator
from core.worker import Worker

class CreditNoteListDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.avoir_model = FactureAvoirModel(self.db_manager)
        self.company_model = CompanyInfoModel(self.db_manager)
        self.client_model = ClientModel(self.db_manager)
        self.facture_model = FactureModel(self.db_manager)
        self.commande_model = CommandeModel(self.db_manager)
        self.thread = None
        self.worker = None
        self.is_task_running = False

        self.ui = Ui_CreditNoteListDialog()
        self.ui.setupUi(self)

        self.setup_table()
        self.setup_connections()
        self.load_data()

    def setup_table(self):
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels([
            'ID', 'Code Avoir', 'Date Création', 'Facture d\'Origine', 'Total TTC', 'Statut FNE'
        ])
        self.ui.avoirs_table_view.setModel(self.table_model)
        self.ui.avoirs_table_view.setColumnHidden(0, True)

        self.ui.certify_button.setEnabled(False)
        self.ui.print_button.setEnabled(False)

    def setup_connections(self):
        self.ui.button_box.rejected.connect(self.reject)
        self.ui.avoirs_table_view.selectionModel().selectionChanged.connect(self.on_selection_changed)
        self.ui.avoirs_table_view.doubleClicked.connect(self.open_avoir_details)
        self.ui.print_button.clicked.connect(self.print_avoir)
        self.ui.certify_button.clicked.connect(self.certify_avoir)

    def certify_avoir(self):
        if self.is_task_running:
            QMessageBox.warning(self, "Tâche en cours", "Une autre tâche est déjà en cours. Veuillez patienter.")
            return

        avoir_id = self.get_selected_avoir_id()
        if not avoir_id: return

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
            QMessageBox.critical(self, "Erreur Critique", "Impossible de trouver l'ID de certification FNE pour la facture d'origine. L'avoir ne peut pas être certifié.")
            return

        commande_id = self.facture_model.get_commande_id_from_facture(original_facture_id)
        if not commande_id:
            QMessageBox.critical(self, "Erreur Critique", "Impossible de trouver la commande d'origine.")
            return
        original_items_with_fne_id = self.commande_model.get_items_with_fne_id(commande_id)

        # On utilise l'ID de la ligne de commande, qui est unique, pour la correspondance.
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
                "quantity": int(item['quantity'])
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

    def on_avoir_certification_finished(self, avoir_id, fne_data):
        self.is_task_running = False
        nim = fne_data.get('nim')
        qr_code = fne_data.get('qr_code')
        QMessageBox.information(self, "Succès", f"Avoir certifié avec succès.\nNIM: {nim}")

        # Mettre à jour le statut dans la base de données
        self.avoir_model.update_fne_status(avoir_id, 'success', nim=nim, qr_code=qr_code)

        self.load_data()
        self.ui.certify_button.setEnabled(True)

    def on_avoir_certification_error(self, avoir_id, error_message):
        self.is_task_running = False
        QMessageBox.critical(self, "Erreur de Certification FNE", error_message)
        self.avoir_model.update_fne_status(avoir_id, 'failed', error_message=error_message)
        self.load_data()
        self.ui.certify_button.setEnabled(True)

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
        self.ui.avoirs_table_view.resizeColumnsToContents()

    def on_selection_changed(self, selected, deselected):
        self.ui.print_button.setEnabled(self.ui.avoirs_table_view.selectionModel().hasSelection())

        should_enable_certify = False
        avoir_id = self.get_selected_avoir_id()

        if avoir_id:
            avoir_data = self.avoir_model.get_by_id(avoir_id)
            # Conditions pour activer le bouton de certification :
            # 1. L'avoir existe.
            # 2. L'avoir n'est pas déjà certifié avec succès.
            # 3. La facture d'origine est liée.
            # 4. La facture d'origine a été certifiée (a un fne_invoice_id).
            if avoir_data and avoir_data.get('statut_fne') != 'success':
                original_facture_id = avoir_data.get('facture_origine_id')
                if original_facture_id:
                    fne_invoice_id = self.facture_model.get_fne_invoice_id(original_facture_id)
                    if fne_invoice_id:
                        should_enable_certify = True

        self.ui.certify_button.setEnabled(should_enable_certify)

    def get_selected_avoir_id(self):
        selected_indexes = self.ui.avoirs_table_view.selectionModel().selectedRows()
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

        # Pour imprimer, on a besoin des infos de l'entreprise et du client.
        company_info = self.company_model.get_first()
        client_info = {
            "name": avoir_data.get('client_name', 'N/A'),
            "address": avoir_data.get('client_address', 'N/A'),
            "contact": avoir_data.get('client_contact', 'N/A')
        }

        generator = PDFGenerator(template_file="avoir.html")
        context = {
            "company": company_info,
            "client": client_info,
            "invoice": avoir_data,  # Le template s'attend à 'invoice'
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
        self.ui.print_button.setEnabled(False)

    def on_printing_finished(self, output_file):
        self.is_task_running = False
        self.ui.print_button.setEnabled(True)
        reply = QMessageBox.information(self, "Impression terminée",
            f"Le document a été exporté : {output_file}\n\nVoulez-vous l'ouvrir ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes)
        if reply == QMessageBox.StandardButton.Yes:
            webbrowser.open(os.path.abspath(output_file))

    def on_printing_error(self, error_message):
        self.is_task_running = False
        self.ui.print_button.setEnabled(True)
        QMessageBox.critical(self, "Erreur d'impression", f"Une erreur est survenue:\n{error_message}")

    # def certify_avoir(self):
    #     pass
