from mysql.connector import Error

class ClientModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all(self):
        """Récupère tous les clients de la base de données."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name, address, email, phone FROM clients ORDER BY name")
            clients = cursor.fetchall()
            return clients
        except Error as e:
            print(f"Erreur lors de la récupération des clients: {e}")
            return []
        finally:
            cursor.close()

    def get_by_id(self, client_id):
        """Récupère un client par son ID."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name, address, email, phone FROM clients WHERE id = %s", (client_id,))
            client = cursor.fetchone()
            return client
        except Error as e:
            print(f"Erreur lors de la récupération du client {client_id}: {e}")
            return None
        finally:
            cursor.close()

    def create(self, client_data):
        """Crée un nouveau client."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        query = "INSERT INTO clients (name, address, email, phone) VALUES (%s, %s, %s, %s)"
        values = (
            client_data.get('name'),
            client_data.get('address'),
            client_data.get('email'),
            client_data.get('phone')
        )
        try:
            cursor.execute(query, values)
            connection.commit()
            print(f"Client '{client_data.get('name')}' créé avec succès.")
            return True
        except Error as e:
            print(f"Erreur lors de la création du client: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()

    def update(self, client_id, client_data):
        """Met à jour un client existant."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        query = """
            UPDATE clients SET name = %s, address = %s, email = %s, phone = %s
            WHERE id = %s
        """
        values = (
            client_data.get('name'),
            client_data.get('address'),
            client_data.get('email'),
            client_data.get('phone'),
            client_id
        )
        try:
            cursor.execute(query, values)
            connection.commit()
            print(f"Client ID {client_id} mis à jour avec succès.")
            return True
        except Error as e:
            print(f"Erreur lors de la mise à jour du client {client_id}: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()

    def delete(self, client_id):
        """Supprime un client."""
        # Attention: vérifier les contraintes de clé étrangère (factures liées)
        # Une meilleure approche serait de "désactiver" le client.
        connection = self.db_manager.get_connection()
        if not connection:
            return False

        cursor = connection.cursor()
        try:
            # Vérifier si des factures sont liées à ce client
            cursor.execute("SELECT id FROM invoices WHERE client_id = %s LIMIT 1", (client_id,))
            if cursor.fetchone():
                print(f"Impossible de supprimer le client {client_id}: des factures lui sont associées.")
                return False

            cursor.execute("DELETE FROM clients WHERE id = %s", (client_id,))
            connection.commit()
            print(f"Client ID {client_id} supprimé avec succès.")
            return True
        except Error as e:
            print(f"Erreur lors de la suppression du client {client_id}: {e}")
            connection.rollback()
            return False
        finally:
            cursor.close()
