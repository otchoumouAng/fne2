from mysql.connector import Error

class PermissionModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all_permissions(self):
        connection = self.db_manager.get_connection()
        if not connection: return []
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM permissions ORDER BY name")
        perms = cursor.fetchall()
        cursor.close()
        return perms

    def get_role_permissions(self, role_id):
        connection = self.db_manager.get_connection()
        if not connection: return []
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT p.id, p.name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            WHERE rp.role_id = %s
        """
        cursor.execute(query, (role_id,))
        perms = cursor.fetchall()
        cursor.close()
        return [p['id'] for p in perms]

    def update_role_permissions(self, role_id, permission_ids):
        connection = self.db_manager.get_connection()
        if not connection: return False, "Erreur connexion"
        cursor = connection.cursor()

        try:
            # Clear existing
            cursor.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))

            # Insert new
            if permission_ids:
                values = [(role_id, perm_id) for perm_id in permission_ids]
                cursor.executemany("INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)", values)

            connection.commit()
            return True, None
        except Error as e:
            connection.rollback()
            return False, str(e)
        finally:
            cursor.close()
