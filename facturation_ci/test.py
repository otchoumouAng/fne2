import mysql.connector
import pandas as pd
import os
from mysql.connector import Error

# Configuration de la base de données mise à jour
db_config = {
    'host': 'localhost',
    'database': 's_facture_plus',
    'user': 'root',          # Changé de admin à root
    'password': 'Admin@1234'
}

def load_file(file_path):
    """Charge un fichier en fonction de son extension (CSV ou Excel)."""
    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext == '.xls':
            # Lecture d'un fichier Excel .xls (nécessite pip install xlrd)
            return pd.read_excel(file_path, engine='xlrd')
        elif ext == '.xlsx':
            # Lecture d'un fichier Excel .xlsx (nécessite pip install openpyxl)
            return pd.read_excel(file_path, engine='openpyxl')
        else:
            # Lecture d'un fichier CSV
            return pd.read_csv(file_path, encoding='latin-1', sep=None, engine='python')
    except ImportError:
        print(f"Erreur : La bibliothèque nécessaire pour lire {ext} est manquante.")
        print(f"Veuillez installer la dépendance avec : pip install {'xlrd' if ext=='.xls' else 'openpyxl'}")
        return None
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier {file_path} : {e}")
        return None

def import_clients(cursor, file_path):
    """Importe les données clients depuis le fichier spécifié."""
    print(f"Chargement des clients depuis {file_path}...")
    df = load_file(file_path)
    
    if df is None:
        return

    try:
        insert_query = """
        INSERT INTO clients (name, address, phone, ncc) 
        VALUES (%s, %s, %s, %s)
        """
        
        count = 0
        for _, row in df.iterrows():
            name = row.get('NomComplet')
            if pd.isna(name) or str(name).strip() == "":
                continue
                
            data = (
                str(name).strip(),
                str(row.get('SituationGeo', '')) if pd.notna(row.get('SituationGeo')) else None,
                str(row.get('Contact', '')) if pd.notna(row.get('Contact')) else None,
                str(row.get('CompteContribuable', '')) if pd.notna(row.get('CompteContribuable')) else None
            )
            cursor.execute(insert_query, data)
            count += 1
        
        print(f"-> {count} clients importés avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'insertion des clients : {e}")

def import_products(cursor, file_path):
    """Importe les données produits depuis le fichier spécifié."""
    print(f"Chargement des produits depuis {file_path}...")
    df = load_file(file_path)
    
    if df is None:
        return

    try:
        insert_query = """
        INSERT INTO products (name, description, unit_price) 
        VALUES (%s, %s, %s)
        """
        
        count = 0
        for _, row in df.iterrows():
            name = row.get('Libelle')
            price = row.get('PrixUnit')
            
            if pd.isna(name) or pd.isna(price):
                continue
            
            product_name = str(name).strip()
            data = (
                product_name,
                product_name,
                float(price)
            )
            cursor.execute(insert_query, data)
            count += 1
            
        print(f"-> {count} produits importés avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'insertion des produits : {e}")

def main():
    connection = None
    try:
        # Connexion à la base de données
        connection = mysql.connector.connect(**db_config)
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            print("Connexion établie. Début de l'importation...\n")
            
            # Chemins d'accès mis à jour selon vos instructions
            path_clients = r"D:\Export client.xls"
            path_produits = r"D:\Export produit.xls"
            
            # 1. Importation des clients
            if os.path.exists(path_clients):
                import_clients(cursor, path_clients)
            else:
                print(f"Fichier introuvable : {path_clients}")
            
            # 2. Importation des produits
            if os.path.exists(path_produits):
                import_products(cursor, path_produits)
            else:
                print(f"Fichier introuvable : {path_produits}")
            
            # Validation des transactions
            connection.commit()
            print("\nOpération terminée.")

    except Error as e:
        print(f"Erreur de connexion MySQL : {e}")
        if connection:
            connection.rollback()
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            print("Connexion MySQL fermée.")

if __name__ == "__main__":
    main()