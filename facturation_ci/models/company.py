from mysql.connector import Error

class CompanyInfoModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_first(self):
        """
        Récupère les informations de la première entreprise trouvée.
        Dans une application réelle, on pourrait vouloir un ID spécifique.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return None

        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM company_info ORDER BY id LIMIT 1"
        try:
            cursor.execute(query)
            company_info = cursor.fetchone()
            return company_info
        except Error as e:
            print(f"Erreur lors de la récupération des informations de l'entreprise: {e}")
            return None
        finally:
            cursor.close()

    def update_or_create(self, company_data):
        """
        Met à jour les informations de l'entreprise si elles existent, sinon les crée.
        """
        connection = self.db_manager.get_connection()
        if not connection:
            return False, "Erreur de connexion BDD"

        existing_company = self.get_first()

        cursor = connection.cursor()
        if existing_company:
            # UPDATE
            query = """
                UPDATE company_info SET 
                    name = %s, address = %s, phone = %s, email = %s, ncc = %s, 
                    point_of_sale = %s, fne_api_key = %s,
                    tax_regime = %s, tax_office = %s, rccm = %s, 
                    bank_details = %s, establishment = %s
                WHERE id = %s
            """
            values = (
                company_data['name'], company_data['address'], company_data['phone'],
                company_data['email'], company_data['ncc'], company_data['point_of_sale'], 
                company_data['fne_api_key'],
                # --- AJOUTS ---
                company_data['tax_regime'], company_data['tax_office'], company_data['rccm'],
                company_data['bank_details'], company_data['establishment'],
                # --- WHERE ID ---
                existing_company['id']
            )
            operation = "mise à jour"
        else:
            # INSERT
            query = """
                INSERT INTO company_info (
                    name, address, phone, email, ncc, point_of_sale, fne_api_key,
                    tax_regime, tax_office, rccm, bank_details, establishment
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            values = (
                company_data['name'], company_data['address'], company_data['phone'],
                company_data['email'], company_data['ncc'], company_data['point_of_sale'], 
                company_data['fne_api_key'],
                company_data['tax_regime'], company_data['tax_office'], company_data['rccm'],
                company_data['bank_details'], company_data['establishment']
            )
            operation = "création"

        try:
            cursor.execute(query, values)
            connection.commit()
            print(f"La {operation} des informations de l'entreprise a réussi.")
            return True, None
        except Error as e:
            connection.rollback()
            error_message = f"Erreur lors de la {operation} des informations de l'entreprise: {e}"
            print(error_message)
            return False, error_message
        finally:
            cursor.close()