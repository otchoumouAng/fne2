from mysql.connector import Error, conversion

class ProductModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all(self):
        """Récupère tous les produits de la base de données."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name, description, unit_price, tax_rate FROM products ORDER BY name")
            products = cursor.fetchall()
            return products
        except Error as e:
            print(f"Erreur lors de la récupération des produits: {e}")
            return []
        finally:
            cursor.close()

    def get_by_id(self, product_id):
        """Récupère un produit par son ID."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id, name, description, unit_price, tax_rate FROM products WHERE id = %s", (product_id,))
            product = cursor.fetchone()
            return product
        except Error as e:
            print(f"Erreur lors de la récupération du produit {product_id}: {e}")
            return None
        finally:
            cursor.close()

    def create(self, product_data):
        """Crée un nouveau produit."""
        connection = self.db_manager.get_connection()
        if not connection:
            return None, "Database connection error"

        cursor = connection.cursor()
        query = "INSERT INTO products (name, description, unit_price, tax_rate) VALUES (%s, %s, %s, %s)"
        try:
            values = (
                product_data.get('name'),
                product_data.get('description'),
                float(product_data.get('unit_price', 0)),
                float(product_data.get('tax_rate', 18.00))
            )
            cursor.execute(query, values)
            connection.commit()
            print(f"Produit '{product_data.get('name')}' créé avec succès.")
            return cursor.lastrowid, None
        except (Error, ValueError) as e:
            error_message = f"Erreur lors de la création du produit: {e}"
            print(error_message)
            connection.rollback()
            return None, str(e)
        finally:
            cursor.close()

    def update(self, product_id, product_data):
        """Met à jour un produit existant."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Database connection error"

        cursor = connection.cursor()
        query = """
            UPDATE products SET name = %s, description = %s, unit_price = %s, tax_rate = %s
            WHERE id = %s
        """
        try:
            values = (
                product_data.get('name'),
                product_data.get('description'),
                float(product_data.get('unit_price')),
                float(product_data.get('tax_rate')),
                product_id
            )
            cursor.execute(query, values)
            connection.commit()
            print(f"Produit ID {product_id} mis à jour avec succès.")
            return True, None
        except (Error, ValueError) as e:
            error_message = f"Erreur lors de la mise à jour du produit {product_id}: {e}"
            print(error_message)
            connection.rollback()
            return False, str(e)
        finally:
            cursor.close()

    def delete(self, product_id):
        """Supprime un produit."""
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Database connection error"

        cursor = connection.cursor()
        try:
            # Vérifier si le produit est utilisé dans une facture
            cursor.execute("SELECT id FROM invoice_items WHERE product_id = %s LIMIT 1", (product_id,))
            if cursor.fetchone():
                error_message = f"Impossible de supprimer le produit {product_id}: il est utilisé dans des factures."
                print(error_message)
                return False, error_message

            cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
            connection.commit()
            print(f"Produit ID {product_id} supprimé avec succès.")
            return True, None
        except Error as e:
            error_message = f"Erreur lors de la suppression du produit {product_id}: {e}"
            print(error_message)
            connection.rollback()
            return False, str(e)
        finally:
            cursor.close()
