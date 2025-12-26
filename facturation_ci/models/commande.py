from mysql.connector import Error
from datetime import datetime

class CommandeModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_with_client_info(self, filter_today=False):
        """Récupère toutes les commandes avec le nom du client, avec un filtre optionnel pour aujourd'hui."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                cmd.id,
                cmd.code_commande,
                cmd.date_commande,
                cmd.total_ttc,
                cmd.statut,
                c.name as client_name
            FROM commandes cmd
            JOIN clients c ON cmd.client_id = c.id
        """
        params = []
        if filter_today:
            query += " WHERE cmd.date_commande = CURDATE()"

        query += " ORDER BY cmd.date_commande DESC, cmd.id DESC"

        try:
            cursor.execute(query, params)
            commandes = cursor.fetchall()
            return commandes
        except Error as e:
            print(f"Erreur lors de la récupération des commandes: {e}")
            return []
        finally:
            cursor.close()

    def get_all_unvoiced(self):
        """
        Récupère toutes les commandes (en cours ou terminées) qui n'ont pas encore été facturées.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                cmd.id,
                cmd.code_commande,
                cmd.date_commande,
                cmd.total_ttc,
                c.name as client_name,
                c.id as client_id
            FROM commandes cmd
            JOIN clients c ON cmd.client_id = c.id
            LEFT JOIN factures f ON cmd.id = f.commande_id
            WHERE f.id IS NULL AND cmd.statut IN ('en_cours', 'terminee')
            ORDER BY cmd.date_commande DESC, cmd.id DESC
        """
        try:
            cursor.execute(query)
            commandes = cursor.fetchall()
            return commandes
        except Error as e:
            print(f"Erreur lors de la récupération des commandes non facturées: {e}")
            return []
        finally:
            cursor.close()

    def get_by_id(self, commande_id):
        """Récupère les détails complets d'une commande, y compris ses lignes d'articles."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        commande_data = {}
        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM commandes WHERE id = %s", (commande_id,))
            commande_data['details'] = cursor.fetchone()
            if not commande_data['details']:
                return None

            cursor.execute("SELECT * FROM commande_items WHERE commande_id = %s", (commande_id,))
            commande_data['items'] = cursor.fetchall()

            return commande_data
        except Error as e:
            print(f"Erreur lors de la récupération de la commande {commande_id}: {e}")
            return None
        finally:
            cursor.close()

    def get_items_with_fne_id(self, commande_id):
        """Récupère les lignes d'une commande avec leur ID FNE."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []
        cursor = connection.cursor(dictionary=True)
        query = "SELECT id, product_id, description, fne_item_id FROM commande_items WHERE commande_id = %s"
        try:
            cursor.execute(query, (commande_id,))
            return cursor.fetchall()
        except Error as e:
            print(f"Erreur lors de la récupération des items FNE pour la commande {commande_id}: {e}")
            return []
        finally:
            cursor.close()

    def _generate_commande_code(self, cursor):
        """Génère un code de commande unique au format AAMMJJSEQ."""
        today = datetime.now()
        date_prefix = today.strftime("%y%m%d")

        query = "SELECT MAX(code_commande) FROM commandes WHERE code_commande LIKE %s"
        cursor.execute(query, (f"{date_prefix}%",))
        last_code = cursor.fetchone()[0]

        if last_code:
            last_seq = int(last_code[-3:])
            new_seq = last_seq + 1
        else:
            new_seq = 1

        return f"{date_prefix}{new_seq:03d}"

    def create(self, commande_data):
        """Crée une nouvelle commande et ses lignes d'articles dans une transaction."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None, "Erreur de connexion à la BDD."

        cursor = connection.cursor()
        try:
            code_commande = self._generate_commande_code(cursor)

            commande_query = """
                INSERT INTO commandes (code_commande, client_id, user_id, date_commande, total_ht, total_tva, total_ttc, statut)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            details = commande_data['details']
            values = (
                code_commande,
                details['client_id'],
                details['user_id'],
                details['date_commande'],
                details['total_ht'],
                details['total_tva'],
                details['total_ttc'],
                details.get('statut', 'en_cours')
            )
            cursor.execute(commande_query, values)
            commande_id = cursor.lastrowid

            items_query = """
                INSERT INTO commande_items (commande_id, product_id, description, quantity, unit_price, tax_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            for item in commande_data['items']:
                item_values = (
                    commande_id, item['product_id'], item['description'],
                    item['quantity'], item['unit_price'], item['tax_rate']
                )
                cursor.execute(items_query, item_values)

            connection.commit()
            print(f"Commande ID {commande_id} ({code_commande}) créée avec succès.")
            return commande_id, None
        except Error as e:
            connection.rollback()
            error_message = f"Erreur transactionnelle lors de la création de la commande: {e}"
            print(error_message)
            return None, error_message
        finally:
            cursor.close()

    def update(self, commande_id, commande_data):
        """Met à jour une commande existante et ses lignes d'articles."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion à la BDD."

        cursor = connection.cursor()
        try:
            update_query = """
                UPDATE commandes
                SET client_id = %s, date_commande = %s, total_ht = %s, total_tva = %s, total_ttc = %s, statut = %s
                WHERE id = %s
            """
            details = commande_data['details']
            values = (
                details['client_id'], details['date_commande'],
                details['total_ht'], details['total_tva'], details['total_ttc'],
                details.get('statut', 'en_cours'),
                commande_id
            )
            cursor.execute(update_query, values)

            cursor.execute("DELETE FROM commande_items WHERE commande_id = %s", (commande_id,))

            items_query = """
                INSERT INTO commande_items (commande_id, product_id, description, quantity, unit_price, tax_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            for item in commande_data['items']:
                item_values = (
                    commande_id, item['product_id'], item['description'],
                    item['quantity'], item['unit_price'], item['tax_rate']
                )
                cursor.execute(items_query, item_values)

            connection.commit()
            print(f"Commande ID {commande_id} mise à jour avec succès.")
            return True, None
        except Error as e:
            connection.rollback()
            error_message = f"Erreur transactionnelle lors de la mise à jour de la commande: {e}"
            print(error_message)
            return False, error_message
        finally:
            cursor.close()

    def delete(self, commande_id):
        """Supprime une commande et ses articles."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion à la BDD."

        cursor = connection.cursor()
        try:
            # La suppression des items est gérée par ON DELETE CASCADE
            cursor.execute("DELETE FROM commandes WHERE id = %s", (commande_id,))
            connection.commit()
            print(f"Commande ID {commande_id} supprimée avec succès.")
            return True, None
        except Error as e:
            connection.rollback()
            error_message = f"Erreur lors de la suppression de la commande: {e}"
            print(error_message)
            return False, error_message
        finally:
            cursor.close()
