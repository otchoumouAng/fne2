from mysql.connector import Error

class InvoiceModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_with_client_info(self):
        """Récupère toutes les factures avec le nom du client."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                i.id,
                i.issue_date,
                i.due_date,
                i.total_amount,
                i.status,
                i.fne_status,
                i.fne_nim,
                c.name as client_name
            FROM invoices i
            JOIN clients c ON i.client_id = c.id
            ORDER BY i.issue_date DESC, i.id DESC
        """
        try:
            cursor.execute(query)
            invoices = cursor.fetchall()
            return invoices
        except Error as e:
            print(f"Erreur lors de la récupération des factures: {e}")
            return []
        finally:
            cursor.close()

    def get_dashboard_stats(self):
        """Récupère les statistiques pour le tableau de bord."""
        connection = self.db_manager.get_connection()
        if not connection:
            return {}

        cursor = connection.cursor(dictionary=True)
        stats = {}
        try:
            # Chiffre d'affaires des 30 derniers jours (factures non-brouillon)
            cursor.execute("""
                SELECT SUM(total_amount) as revenue
                FROM invoices
                WHERE status != 'draft' AND status != 'cancelled' AND issue_date >= CURDATE() - INTERVAL 30 DAY
            """)
            result = cursor.fetchone()
            stats['revenue_last_30_days'] = result['revenue'] if result['revenue'] else 0

            # Nombre de factures ce mois-ci
            cursor.execute("""
                SELECT COUNT(id) as count
                FROM invoices
                WHERE MONTH(issue_date) = MONTH(CURDATE()) AND YEAR(issue_date) = YEAR(CURDATE())
            """)
            result = cursor.fetchone()
            stats['invoices_this_month'] = result['count']

            # Résumé des statuts
            cursor.execute("""
                SELECT status, COUNT(id) as count
                FROM invoices
                GROUP BY status
            """)
            stats['status_summary'] = {row['status']: row['count'] for row in cursor.fetchall()}

            return stats
        except Error as e:
            print(f"Erreur lors de la récupération des statistiques du dashboard: {e}")
            return {}
        finally:
            cursor.close()

    def get_revenue_per_month(self, months=6):
        """Récupère le chiffre d'affaires par mois pour les 'months' derniers mois."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT
                DATE_FORMAT(issue_date, '%b') as month_name,
                SUM(total_amount) as revenue,
                YEAR(issue_date) as year,
                MONTH(issue_date) as month_num
            FROM invoices
            WHERE status != 'draft' AND status != 'cancelled'
              AND issue_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH)
            GROUP BY YEAR(issue_date), MONTH(issue_date), DATE_FORMAT(issue_date, '%b')
            ORDER BY YEAR(issue_date) ASC, MONTH(issue_date) ASC
        """
        try:
            cursor.execute(query, (months,))
            results = cursor.fetchall()
            # Convertir en liste de tuples (Mois, Revenu)
            data = [(row['month_name'], float(row['revenue'])) for row in results]

            # Si pas assez de données, on pourrait vouloir remplir les mois vides,
            # mais pour l'instant on retourne juste ce qu'on a.
            return data
        except Error as e:
            print(f"Erreur lors de la récupération du CA par mois: {e}")
            return []
        finally:
            cursor.close()

    def get_by_id(self, invoice_id):
        """Récupère les détails complets d'une facture, y compris ses lignes d'articles."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        invoice_data = {}
        cursor = connection.cursor(dictionary=True)
        try:
            # Récupérer les données principales de la facture
            cursor.execute("SELECT * FROM invoices WHERE id = %s", (invoice_id,))
            invoice_data['details'] = cursor.fetchone()
            if not invoice_data['details']:
                return None

            # Récupérer les lignes d'articles
            cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = %s", (invoice_id,))
            invoice_data['items'] = cursor.fetchall()

            return invoice_data
        except Error as e:
            print(f"Erreur lors de la récupération de la facture {invoice_id}: {e}")
            return None
        finally:
            cursor.close()

    def create(self, invoice_data):
        """Crée une nouvelle facture et ses lignes d'articles dans une transaction."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None, "Erreur de connexion à la BDD."

        cursor = connection.cursor()
        try:
            # La transaction est démarrée implicitement par mysql-connector
            # La ligne connection.start_transaction() était redondante.

            # 1. Insérer dans la table 'invoices'
            invoice_query = """
                INSERT INTO invoices (client_id, user_id, document_type, issue_date, due_date, total_amount, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            invoice_details = invoice_data['details']
            invoice_values = (
                invoice_details['client_id'],
                invoice_details['user_id'],
                invoice_details.get('document_type', 'sale'),
                invoice_details['issue_date'],
                invoice_details['due_date'],
                invoice_details['total_amount'],
                'draft' # Toujours créée en tant que brouillon
            )
            cursor.execute(invoice_query, invoice_values)
            invoice_id = cursor.lastrowid

            # 2. Insérer dans la table 'invoice_items'
            items_query = """
                INSERT INTO invoice_items (invoice_id, product_id, description, quantity, unit_price, tax_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            for item in invoice_data['items']:
                item_values = (
                    invoice_id,
                    item['product_id'],
                    item['description'],
                    item['quantity'],
                    item['unit_price'],
                    item['tax_rate']
                )
                cursor.execute(items_query, item_values)

            connection.commit()
            print(f"Facture ID {invoice_id} créée avec succès.")
            return invoice_id, None
        except Error as e:
            connection.rollback()
            error_message = f"Erreur transactionnelle lors de la création de la facture: {e}"
            print(error_message)
            return None, error_message
        finally:
            cursor.close()

    def update(self, invoice_id, invoice_data):
        """Met à jour une facture existante et ses lignes d'articles dans une transaction."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion à la BDD."

        cursor = connection.cursor()
        try:
            # 1. Mettre à jour la table 'invoices'
            update_query = """
                UPDATE invoices
                SET client_id = %s, issue_date = %s, due_date = %s, total_amount = %s
                WHERE id = %s
            """
            invoice_details = invoice_data['details']
            invoice_values = (
                invoice_details['client_id'],
                invoice_details['issue_date'],
                invoice_details['due_date'],
                invoice_details['total_amount'],
                invoice_id
            )
            cursor.execute(update_query, invoice_values)

            # 2. Supprimer les anciens 'invoice_items'
            cursor.execute("DELETE FROM invoice_items WHERE invoice_id = %s", (invoice_id,))

            # 3. Insérer les nouveaux 'invoice_items'
            items_query = """
                INSERT INTO invoice_items (invoice_id, product_id, description, quantity, unit_price, tax_rate)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            for item in invoice_data['items']:
                item_values = (
                    invoice_id,
                    item['product_id'],
                    item['description'],
                    item['quantity'],
                    item['unit_price'],
                    item['tax_rate']
                )
                cursor.execute(items_query, item_values)

            connection.commit()
            print(f"Facture ID {invoice_id} mise à jour avec succès.")
            return True, None
        except Error as e:
            connection.rollback()
            error_message = f"Erreur transactionnelle lors de la mise à jour de la facture: {e}"
            print(error_message)
            return False, error_message
        finally:
            cursor.close()

    def update_fne_data(self, invoice_id, fne_status, nim=None, qr_code=None, error_message=None):
        """Met à jour le statut et les données FNE d'une facture."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        query = """
            UPDATE invoices
            SET fne_status = %s, fne_nim = %s, fne_qr_code = %s, fne_error_message = %s, status = IF(%s='success', 'certified', status)
            WHERE id = %s
        """
        values = (fne_status, nim, qr_code, error_message, fne_status, invoice_id)
        try:
            cursor.execute(query, values)
            connection.commit()
            print(f"Données FNE pour la facture {invoice_id} mises à jour.")
            return True
        except Error as e:
            print(f"Erreur lors de la mise à jour FNE pour la facture {invoice_id}: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
