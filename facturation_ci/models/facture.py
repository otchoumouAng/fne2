from mysql.connector import Error
from datetime import datetime

class FactureModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_with_details(self):
        """
        Récupère toutes les factures avec des détails joints depuis
        les commandes et les clients pour l'affichage.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        # Cette requête joint factures, commandes, et clients
        query = """
            SELECT
                f.id,
                f.code_facture,
                f.date_facturation,
                f.statut_fne,
                cmd.code_commande,
                cmd.total_ttc,
                c.name as client_name
            FROM factures f
            JOIN commandes cmd ON f.commande_id = cmd.id
            JOIN clients c ON cmd.client_id = c.id
            ORDER BY f.date_facturation DESC, f.id DESC
        """
        try:
            cursor.execute(query)
            factures = cursor.fetchall()
            return factures
        except Error as e:
            print(f"Erreur lors de la récupération des factures: {e}")
            return []
        finally:
            cursor.close()

    def create_from_commande(self, commande_id):
        """
        Crée une facture et un BL à partir d'un ID de commande dans une transaction.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None, "Erreur de connexion à la BDD."

        cursor = connection.cursor(dictionary=True)
        try:
            # 1. Récupérer le code de la commande pour l'utiliser dans les codes facture/BL
            cursor.execute("SELECT code_commande FROM commandes WHERE id = %s", (commande_id,))
            commande = cursor.fetchone()
            if not commande:
                return None, f"Commande ID {commande_id} non trouvée."

            code_commande = commande['code_commande']
            code_facture = f"F-{code_commande}"
            code_bl = f"BL-{code_commande}"

            # 2. Insérer la nouvelle facture
            facture_query = """
                INSERT INTO factures (code_facture, commande_id, date_facturation)
                VALUES (%s, %s, %s)
            """
            today = datetime.now().date()
            cursor.execute(facture_query, (code_facture, commande_id, today))
            facture_id = cursor.lastrowid

            # 3. Insérer le nouveau Bordereau de Livraison
            bl_query = """
                INSERT INTO bordereaux_livraison (code_bl, facture_id, date_creation)
                VALUES (%s, %s, %s)
            """
            now = datetime.now()
            cursor.execute(bl_query, (code_bl, facture_id, now))

            connection.commit()
            print(f"Facture {code_facture} et BL {code_bl} créés avec succès pour la commande ID {commande_id}.")
            return facture_id, None
        except Error as e:
            connection.rollback()
            # Gérer le cas où la facture existe déjà (contrainte UNIQUE sur commande_id)
            if e.errno == 1062: # Duplicate entry
                error_message = f"Une facture existe déjà pour la commande ID {commande_id}."
            else:
                error_message = f"Erreur transactionnelle lors de la création de la facture: {e}"
            print(error_message)
            return None, error_message
        finally:
            cursor.close()

    def save_certification_results(self, facture_id, nim, qr_code, fne_invoice_id, fne_created_at, items_id_map):
        """
        Sauvegarde tous les résultats d'une certification FNE réussie dans une transaction atomique.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion BDD"

        cursor = connection.cursor()
        try:
            certification_datetime = datetime.fromisoformat(fne_created_at.replace('Z', '+00:00')) if fne_created_at else None
            # 1. Mettre à jour la facture avec toutes les données FNE
            update_facture_query = """
                UPDATE factures
                SET statut_fne = 'success', fne_nim = %s, fne_qr_code = %s, fne_invoice_id = %s, date_et_heure_de_certification = %s, fne_error_message = NULL
                WHERE id = %s
            """
            cursor.execute(update_facture_query, (nim, qr_code, fne_invoice_id, certification_datetime, facture_id))

            # 2. Mettre à jour chaque ligne de commande avec son ID FNE
            if items_id_map:
                update_item_query = "UPDATE commande_items SET fne_item_id = %s WHERE id = %s"
                cursor.executemany(update_item_query, items_id_map)

            # 3. Mettre à jour le statut de la commande liée à 'terminee'
            # On récupère d'abord l'ID de la commande
            cursor.execute("SELECT commande_id FROM factures WHERE id = %s", (facture_id,))
            result = cursor.fetchone()
            if result:
                commande_id = result[0]
                update_commande_query = "UPDATE commandes SET statut = 'terminee' WHERE id = %s"
                cursor.execute(update_commande_query, (commande_id,))

            connection.commit()
            print(f"Résultats de certification FNE pour la facture {facture_id} sauvegardés avec succès.")
            return True, None
        except Error as e:
            connection.rollback()
            error_message = f"Erreur lors de la sauvegarde des résultats de certification FNE pour la facture {facture_id}: {e}"
            print(error_message)
            return False, error_message
        finally:
            cursor.close()

    def save_certification_error(self, facture_id, error_message):
        """Met à jour le statut FNE d'une facture en cas d'échec."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion BDD"

        cursor = connection.cursor()
        query = """
            UPDATE factures
            SET statut_fne = 'failed', fne_error_message = %s
            WHERE id = %s
        """
        try:
            cursor.execute(query, (error_message, facture_id))
            connection.commit()
            return True, None
        except Error as e:
            connection.rollback()
            return False, str(e)
        finally:
            cursor.close()

    def get_fne_invoice_id(self, facture_id):
        """
        Récupère l'ID FNE d'une facture si et seulement si son statut de certification est 'success'.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None
        cursor = connection.cursor()
        query = "SELECT fne_invoice_id FROM factures WHERE id = %s AND statut_fne = 'success'"
        try:
            cursor.execute(query, (facture_id,))
            result = cursor.fetchone()
            # On vérifie aussi que le résultat n'est pas None ou une chaîne vide
            return result[0] if result and result[0] else None
        except Error as e:
            print(f"Erreur lors de la récupération de l'ID FNE pour la facture {facture_id}: {e}")
            return None
        finally:
            cursor.close()

    def get_commande_id_from_facture(self, facture_id):
        """Récupère l'ID de la commande associée à une facture."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor()
        query = "SELECT commande_id FROM factures WHERE id = %s"
        try:
            cursor.execute(query, (facture_id,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Error as e:
            print(f"Erreur lors de la récupération de l'ID de commande pour la facture {facture_id}: {e}")
            return None
        finally:
            cursor.close()

    def get_by_id_for_printing(self, facture_id):
        """
        Récupère les détails complets d'une facture et de sa commande
        associée pour des opérations comme l'impression.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        data = {}
        cursor = connection.cursor(dictionary=True)
        try:
            # Récupérer les détails de la facture et de la commande
            query = """
                SELECT 
                f.*, 
                bl.code_bl, bl.date_creation as bl_date_creation,
                cmd.code_commande, cmd.date_commande, cmd.total_ht, cmd.total_tva, cmd.total_ttc,
                c.id as client_id, c.name as client_name, c.address as client_address, 
                c.email as client_email, c.phone as client_phone, c.ncc as client_ncc
            FROM factures f
            LEFT JOIN bordereaux_livraison bl ON f.id = bl.facture_id
            JOIN commandes cmd ON f.commande_id = cmd.id
            JOIN clients c ON cmd.client_id = c.id
            WHERE f.id = %s
            """
            cursor.execute(query, (facture_id,))
            data['details'] = cursor.fetchone()
            if not data['details']:
                return None

            # Récupérer les lignes d'articles depuis la commande
            commande_id = data['details']['commande_id']
            cursor.execute("SELECT * FROM commande_items WHERE commande_id = %s", (commande_id,))
            data['items'] = cursor.fetchall()

            return data
        except Error as e:
            print(f"Erreur lors de la récupération de la facture {facture_id} pour impression: {e}")
            return None
        finally:
            cursor.close()
