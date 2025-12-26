from mysql.connector import Error

class BordereauLivraisonModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_by_facture_id(self, facture_id):
        """
        Récupère les détails d'un BL et les informations associées (facture, commande, client, items)
        à partir d'un ID de facture.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        data = {}
        cursor = connection.cursor(dictionary=True)
        try:
            # Cette requête complexe joint toutes les tables nécessaires
            query = """
                SELECT
                    bl.id as bl_id, bl.code_bl, bl.date_creation as bl_date_creation, bl.statut_fne,
                    f.id as facture_id, f.code_facture, f.date_facturation,
                    cmd.id as commande_id, cmd.code_commande, cmd.date_commande,
                    c.id as client_id, c.name as client_name, c.address as client_address,
                    c.email as client_email, c.phone as client_phone
                FROM bordereaux_livraison bl
                JOIN factures f ON bl.facture_id = f.id
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
            item_query = "SELECT id, product_id, description, quantity, unit_price, tax_rate, fne_item_id FROM commande_items WHERE commande_id = %s"
            cursor.execute(item_query, (commande_id,))
            data['items'] = cursor.fetchall()

            return data
        except Error as e:
            print(f"Erreur lors de la récupération du BL pour la facture {facture_id}: {e}")
            return None
        finally:
            cursor.close()

    def update_fne_status(self, bl_id, statut_fne, nim=None, qr_code=None, error_message=None):
        """Met à jour le statut et les données FNE d'un BL."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion BDD"

        cursor = connection.cursor()
        query = """
            UPDATE bordereaux_livraison
            SET statut_fne = %s, fne_nim = %s, fne_qr_code = %s, fne_error_message = %s
            WHERE id = %s
        """
        values = (statut_fne, nim, qr_code, error_message, bl_id)
        try:
            cursor.execute(query, values)
            connection.commit()
            print(f"Données FNE pour le BL {bl_id} mises à jour.")
            return True, None
        except Error as e:
            print(f"Erreur lors de la mise à jour FNE pour le BL {bl_id}: {e}")
            connection.rollback()
            return False, str(e)
        finally:
            cursor.close()
