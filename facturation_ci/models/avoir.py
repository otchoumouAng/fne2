import json
from mysql.connector import Error
from datetime import datetime

class FactureAvoirModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all(self):
        """Récupère toutes les factures d'avoir avec quelques détails joints."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        # Jointure pour récupérer le code de la facture d'origine
        query = """
            SELECT
                fa.id, fa.code_avoir, fa.date_creation, fa.total_ttc, fa.statut_fne,
                f.code_facture as code_facture_origine
            FROM factures_avoir fa
            JOIN factures f ON fa.facture_origine_id = f.id
            ORDER BY fa.date_creation DESC, fa.id DESC
        """
        try:
            cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            print(f"Erreur lors de la récupération des avoirs: {e}")
            return []
        finally:
            cursor.close()

    def update_fne_status(self, avoir_id, statut_fne, nim=None, qr_code=None, error_message=None, fne_created_at=None):
        """Met à jour le statut et les données FNE d'un avoir."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion BDD"

        cursor = connection.cursor()
        query = """
            UPDATE factures_avoir
            SET statut_fne = %s, fne_nim = %s, fne_qr_code = %s, fne_error_message = %s, date_et_heure_de_certification = %s
            WHERE id = %s
        """
        certification_datetime = datetime.fromisoformat(fne_created_at.replace('Z', '+00:00')) if fne_created_at else None
        values = (statut_fne, nim, qr_code, error_message, certification_datetime, avoir_id)
        try:
            cursor.execute(query, values)
            connection.commit()
            print(f"Données FNE pour l'avoir {avoir_id} mises à jour.")
            return True, None
        except Error as e:
            print(f"Erreur lors de la mise à jour FNE pour l'avoir {avoir_id}: {e}")
            connection.rollback()
            return False, str(e)
        finally:
            cursor.close()

    def get_by_id(self, avoir_id):
        """Récupère les détails complets d'un avoir, y compris les infos client."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                fa.*,
                f.code_facture as code_facture_origine,
                f.fne_nim as fne_nim_origine,
                c.name as client_name,
                c.address as client_address,
                c.phone as client_contact,
                c.email as client_email
            FROM factures_avoir fa
            JOIN factures f ON fa.facture_origine_id = f.id
            JOIN commandes cmd ON f.commande_id = cmd.id
            JOIN clients c ON cmd.client_id = c.id
            WHERE fa.id = %s
        """
        try:
            cursor.execute(query, (avoir_id,))
            avoir_data = cursor.fetchone()
            # Le champ lignes_avoir est en JSON, on le décode
            if avoir_data and 'lignes_avoir' in avoir_data:
                avoir_data['lignes_avoir'] = json.loads(avoir_data['lignes_avoir'])
            return avoir_data
        except Error as e:
            print(f"Erreur lors de la récupération de l'avoir ID {avoir_id}: {e}")
            return None
        finally:
            cursor.close()

    def create(self, original_facture_id, code_facture_origine, avoir_items, totals):
        """
        Crée une nouvelle facture d'avoir dans la base de données.

        :param original_facture_id: ID de la facture d'origine.
        :param code_facture_origine: Code de la facture d'origine pour le code de l'avoir.
        :param avoir_items: Liste des dictionnaires d'articles pour l'avoir.
        :param totals: Dictionnaire contenant total_ht, total_tva, total_ttc.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None, "Erreur de connexion à la BDD."

        cursor = connection.cursor()
        try:
            # Générer un code d'avoir unique
            # Pourrait être plus robuste en vérifiant l'unicité dans une boucle
            code_avoir = f"AV-{code_facture_origine}"

            query = """
                INSERT INTO factures_avoir
                (code_avoir, facture_origine_id, date_creation, lignes_avoir, total_ht, total_tva, total_ttc)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """

            today = datetime.now().date()
            items_json = json.dumps(avoir_items) # Convertir la liste d'items en chaîne JSON

            values = (
                code_avoir,
                original_facture_id,
                today,
                items_json,
                totals['total_ht'],
                totals['total_tva'],
                totals['total_ttc']
            )

            cursor.execute(query, values)
            avoir_id = cursor.lastrowid
            connection.commit()

            print(f"Facture d'avoir ID {avoir_id} ({code_avoir}) créée avec succès.")
            return avoir_id, None

        except Error as e:
            connection.rollback()
            error_message = f"Erreur lors de la création de la facture d'avoir: {e}"
            print(error_message)
            return None, error_message
        finally:
            cursor.close()
