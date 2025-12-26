import mysql.connector
from mysql.connector import Error
import sys

class DBManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # The __init__ will be called every time, but we only connect once.
        if not hasattr(self, 'connection') or self.connection is None:
            self.host = "127.0.0.1"
            self.database = "s_facture_plus"
            self.user = "root"
            self.password = "Admin@1234"  
            self.connection = None
            # La connexion n'est pas établie ici, mais au premier appel de get_connection

    def connect(self):
        """Établit la connexion à la base de données. Lève une ConnectionError en cas d'échec."""
        if self.connection and self.connection.is_connected():
            return

        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            print("Connexion à la base de données réussie.")
        except Error as e:
            print(f"Erreur de connexion à la base de données : {e}")
            self.connection = None
            raise ConnectionError(f"Impossible de se connecter à la base de données: {e}")

    def get_connection(self):
        """Retourne l'objet de connexion. Tente de se connecter si nécessaire."""
        if not self.connection or not self.connection.is_connected():
            # print("Connexion non établie ou perdue. Tentative de connexion...")
            self.connect()
        return self.connection

    def close(self):
        """Ferme la connexion à la base de données."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            print("Connexion à la base de données fermée.")

# Exemple d'utilisation (Singleton)
# from db_manager import DBManager
# db = DBManager(host='localhost', database='facturation_db', user='user', password='password')
# connection = db.get_connection()
# if connection:
#     cursor = connection.cursor()
#     # ... faire quelque chose
#     db.close()
