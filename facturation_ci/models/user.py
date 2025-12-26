from mysql.connector import Error
import bcrypt

class UserModel:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_all(self):
        """Récupère tous les utilisateurs avec leur rôle."""
        connection = self.db_manager.get_connection()
        if not connection:
            return []
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT u.id, u.username, u.full_name, u.role_id, r.name as role_name, u.is_active
            FROM users u
            JOIN roles r ON u.role_id = r.id
            ORDER BY u.id ASC
        """
        cursor.execute(query)
        users = cursor.fetchall()
        cursor.close()
        return users

    def get_by_id(self, user_id):
        connection = self.db_manager.get_connection()
        if not connection: return None
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user

    def create(self, data):
        connection = self.db_manager.get_connection()
        if not connection: return False, "Erreur connexion"
        cursor = connection.cursor()

        try:
            hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            query = """
                INSERT INTO users (username, password_hash, full_name, role_id, is_active)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (
                data['username'],
                hashed_pw,
                data['full_name'],
                data['role_id'],
                data.get('is_active', True)
            ))
            connection.commit()
            return True, None
        except Error as e:
            return False, str(e)
        finally:
            cursor.close()

    def update(self, user_id, data):
        connection = self.db_manager.get_connection()
        if not connection: return False, "Erreur connexion"
        cursor = connection.cursor()

        try:
            if data.get('password'):
                hashed_pw = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                query = """
                    UPDATE users
                    SET username=%s, password_hash=%s, full_name=%s, role_id=%s, is_active=%s
                    WHERE id=%s
                """
                values = (data['username'], hashed_pw, data['full_name'], data['role_id'], data.get('is_active', True), user_id)
            else:
                query = """
                    UPDATE users
                    SET username=%s, full_name=%s, role_id=%s, is_active=%s
                    WHERE id=%s
                """
                values = (data['username'], data['full_name'], data['role_id'], data.get('is_active', True), user_id)

            cursor.execute(query, values)
            connection.commit()
            return True, None
        except Error as e:
            return False, str(e)
        finally:
            cursor.close()

    def delete(self, user_id):
        connection = self.db_manager.get_connection()
        if not connection: return False, "Erreur connexion"
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            return True, None
        except Error as e:
            return False, str(e)
        finally:
            cursor.close()

    def get_roles(self):
        connection = self.db_manager.get_connection()
        if not connection: return []
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM roles ORDER BY name")
        roles = cursor.fetchall()
        cursor.close()
        return roles

    def get_user_permissions(self, user_id):
        """Récupère la liste des noms de permissions pour un utilisateur donné."""
        connection = self.db_manager.get_connection()
        if not connection: return []

        cursor = connection.cursor()
        query = """
            SELECT p.name
            FROM permissions p
            JOIN role_permissions rp ON p.id = rp.permission_id
            JOIN users u ON rp.role_id = u.role_id
            WHERE u.id = %s
        """
        cursor.execute(query, (user_id,))
        permissions = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return permissions
