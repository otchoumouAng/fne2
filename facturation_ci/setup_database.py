import mysql.connector
from mysql.connector import Error
import getpass
import bcrypt

def create_database(cursor, db_name):
    """Crée la base de données si elle n'existe pas."""
    try:
        cursor.execute(f"CREATE DATABASE {db_name} DEFAULT CHARACTER SET 'utf8mb4'")
        print(f"Base de données '{db_name}' créée avec succès.")
    except Error as e:
        if e.errno == 1007: # Can't create database; database exists
            print(f"La base de données '{db_name}' existe déjà.")
        else:
            raise

def create_tables(cursor):
    """Crée les tables du projet."""
    TABLES = {}

    TABLES['roles'] = (
        "CREATE TABLE `roles` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `name` VARCHAR(50) NOT NULL UNIQUE COMMENT 'Ex: Admin, Comptable, Vendeur'"
        ") ENGINE=InnoDB")

    TABLES['users'] = (
        "CREATE TABLE `users` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `username` VARCHAR(100) NOT NULL UNIQUE,"
        "  `password_hash` VARCHAR(255) NOT NULL,"
        "  `full_name` VARCHAR(255),"
        "  `role_id` INT NOT NULL,"
        "  `is_active` BOOLEAN DEFAULT TRUE,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['company_info'] = (
        "CREATE TABLE `company_info` ("
        "    `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "    `name` VARCHAR(255) NOT NULL,"
        "    `address` TEXT,"
        "    `phone` VARCHAR(50),"
        "    `email` VARCHAR(100),"
        "    `ncc` VARCHAR(100) COMMENT 'N° de contribuable',"
        "    `point_of_sale` VARCHAR(255) NULL,"
        "    `fne_api_key` VARCHAR(255) COMMENT 'Clé d''API pour FNE',"
        "    `tax_regime` VARCHAR(100) COMMENT 'Régime d''imposition',"
        "    `tax_office` VARCHAR(255) COMMENT 'Centre des impôts',"
        "    `rccm` VARCHAR(255) COMMENT 'N° RCCM',"
        "    `bank_details` VARCHAR(255) COMMENT 'Références bancaires',"
        "    `establishment` VARCHAR(255) COMMENT 'Établissement'"
        ") ENGINE=InnoDB")

    TABLES['clients'] = (
        "CREATE TABLE `clients` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `name` VARCHAR(255) NOT NULL,"
        "  `address` TEXT,"
        "  `email` VARCHAR(100),"
        "  `phone` VARCHAR(50),"
        "  `ncc` VARCHAR(100) NULL COMMENT 'N° de contribuable',"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  `tax_regime` VARCHAR(100) NULL COMMENT 'Régime d''imposition'"
        ") ENGINE=InnoDB")

    TABLES['products'] = (
        "CREATE TABLE `products` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `name` VARCHAR(255) NOT NULL,"
        "  `description` TEXT,"
        "  `unit_price` DECIMAL(15, 2) NOT NULL,"
        "  `tax_rate` INT DEFAULT 18 COMMENT 'Taux de TVA en pourcentage'"
        ") ENGINE=InnoDB")

    # --- NOUVELLE ARCHITECTURE: COMMANDE -> FACTURE ---

    TABLES['commandes'] = (
        "CREATE TABLE `commandes` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `code_commande` VARCHAR(9) NOT NULL UNIQUE,"
        "  `client_id` INT NOT NULL,"
        "  `user_id` INT NOT NULL,"
        "  `date_commande` DATE NOT NULL,"
        "  `total_ht` DECIMAL(15, 2) NOT NULL,"
        "  `total_tva` DECIMAL(15, 2) NOT NULL,"
        "  `total_ttc` DECIMAL(15, 2) NOT NULL,"
        "  `statut` ENUM('en_cours', 'terminee', 'annulee') NOT NULL DEFAULT 'en_cours',"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`client_id`) REFERENCES `clients`(`id`),"
        "  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['commande_items'] = (
        "CREATE TABLE `commande_items` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `commande_id` INT NOT NULL,"
        "  `product_id` INT NOT NULL,"
        "  `description` VARCHAR(255) NOT NULL,"
        "  `quantity` INT NOT NULL,"
        "  `unit_price` DECIMAL(15, 2) NOT NULL,"
        "  `tax_rate` DECIMAL(5, 2) NOT NULL,"
        "  `fne_item_id` VARCHAR(255) NULL COMMENT 'ID unique de la ligne d''article retourné par FNE',"
        "  FOREIGN KEY (`commande_id`) REFERENCES `commandes`(`id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['factures'] = (
        "CREATE TABLE `factures` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `code_facture` VARCHAR(255) NOT NULL UNIQUE,"
        "  `commande_id` INT NOT NULL UNIQUE,"
        "  `date_facturation` DATE NOT NULL,"
        "  `statut_fne` ENUM('pending', 'success', 'failed') DEFAULT 'pending',"
        "  `fne_nim` VARCHAR(255) NULL,"
        "  `fne_invoice_id` VARCHAR(255) NULL COMMENT 'ID unique de la facture retourné par FNE',"
        "  `fne_qr_code` TEXT NULL,"
        "  `fne_error_message` TEXT NULL,"
        "  `date_et_heure_de_certification` DATETIME NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`commande_id`) REFERENCES `commandes`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['bordereaux_livraison'] = (
        "CREATE TABLE `bordereaux_livraison` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `code_bl` VARCHAR(255) NOT NULL UNIQUE,"
        "  `facture_id` INT NOT NULL UNIQUE,"
        "  `date_creation` DATETIME NOT NULL,"
        "  `statut_fne` ENUM('pending', 'success', 'failed') DEFAULT 'pending',"
        "  `fne_nim` VARCHAR(255) NULL,"
        "  `fne_qr_code` TEXT NULL,"
        "  `fne_error_message` TEXT NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`facture_id`) REFERENCES `factures`(`id`)"
        ") ENGINE=InnoDB")

    TABLES['factures_avoir'] = (
        "CREATE TABLE `factures_avoir` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `code_avoir` VARCHAR(255) NOT NULL UNIQUE,"
        "  `facture_origine_id` INT NOT NULL,"
        "  `date_creation` DATE NOT NULL,"
        "  `lignes_avoir` JSON NOT NULL,"
        "  `total_ht` DECIMAL(15, 2) NOT NULL,"
        "  `total_tva` DECIMAL(15, 2) NOT NULL,"
        "  `total_ttc` DECIMAL(15, 2) NOT NULL,"
        "  `statut_fne` ENUM('pending', 'success', 'failed') DEFAULT 'pending',"
        "  `fne_nim` VARCHAR(255) NULL,"
        "  `fne_qr_code` TEXT NULL,"
        "  `fne_error_message` TEXT NULL,"
        "  `date_et_heure_de_certification` DATETIME NULL,"
        "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "  FOREIGN KEY (`facture_origine_id`) REFERENCES `factures`(`id`)"
        ") ENGINE=InnoDB")

    # --- ANCIENNE STRUCTURE (CONSERVÉE POUR L'HISTORIQUE) ---

    # TABLES['invoices'] = (
    #     "CREATE TABLE `invoices` ("
    #     "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    #     "  `client_id` INT NOT NULL,"
    #     "  `user_id` INT NOT NULL,"
    #     "  `document_type` ENUM('sale', 'refund', 'purchase') NOT NULL,"
    #     "  `issue_date` DATE NOT NULL,"
    #     "  `due_date` DATE,"
    #     "  `total_amount` DECIMAL(15, 2) NOT NULL,"
    #     "  `status` ENUM('draft', 'certified', 'paid', 'partially_paid', 'cancelled') NOT NULL DEFAULT 'draft',"
    #     "  `fne_status` ENUM('pending', 'success', 'failed') DEFAULT 'pending',"
    #     "  `fne_nim` VARCHAR(255) NULL,"
    #     "  `fne_qr_code` TEXT NULL,"
    #     "  `fne_error_message` TEXT NULL,"
    #     "  `original_invoice_id` INT NULL,"
    #     "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
    #     "  FOREIGN KEY (`client_id`) REFERENCES `clients`(`id`),"
    #     "  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`),"
    #     "  FOREIGN KEY (`original_invoice_id`) REFERENCES `invoices`(`id`)"
    #     ") ENGINE=InnoDB")

    # TABLES['invoice_items'] = (
    #     "CREATE TABLE `invoice_items` ("
    #     "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    #     "  `invoice_id` INT NOT NULL,"
    #     "  `product_id` INT NOT NULL,"
    #     "  `description` VARCHAR(255) NOT NULL,"
    #     "  `quantity` DECIMAL(10, 2) NOT NULL,"
    #     "  `unit_price` DECIMAL(15, 2) NOT NULL,"
    #     "  `tax_rate` DECIMAL(5, 2) NOT NULL,"
    #     "  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`) ON DELETE CASCADE,"
    #     "  FOREIGN KEY (`product_id`) REFERENCES `products`(`id`)"
    #     ") ENGINE=InnoDB")

    # TABLES['payments'] = (
    #     "CREATE TABLE `payments` ("
    #     "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
    #     "  `invoice_id` INT NOT NULL,"
    #     "  `payment_date` DATE NOT NULL,"
    #     "  `amount` DECIMAL(15, 2) NOT NULL,"
    #     "  `payment_method` VARCHAR(50),"
    #     "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
    #     "  FOREIGN KEY (`invoice_id`) REFERENCES `invoices`(`id`)"
    #     ") ENGINE=InnoDB")

    TABLES['permissions'] = (
        "CREATE TABLE `permissions` ("
        "  `id` INT AUTO_INCREMENT PRIMARY KEY,"
        "  `name` VARCHAR(255) NOT NULL UNIQUE COMMENT 'Ex: clients.view, invoices.create'"
        ") ENGINE=InnoDB")

    TABLES['role_permissions'] = (
        "CREATE TABLE `role_permissions` ("
        "  `role_id` INT NOT NULL,"
        "  `permission_id` INT NOT NULL,"
        "  PRIMARY KEY (`role_id`, `permission_id`),"
        "  FOREIGN KEY (`role_id`) REFERENCES `roles`(`id`) ON DELETE CASCADE,"
        "  FOREIGN KEY (`permission_id`) REFERENCES `permissions`(`id`) ON DELETE CASCADE"
        ") ENGINE=InnoDB")

    print("Création des tables...")
    for table_name in TABLES:
        table_sql = TABLES[table_name]
        try:
            print(f"  - Création de la table '{table_name}'... ", end='')
            cursor.execute(table_sql)
            print("OK")
        except Error as e:
            if e.errno == 1050: # Table already exists
                print("déjà existante.")
            else:
                print(f"ERREUR: {e}")
                raise

def insert_initial_data(cursor):
    """Insère les données initiales (rôles et admin)."""
    print("\nInsertion des données initiales...")

    # --- Rôles ---
    roles = [('Admin',), ('Comptable',), ('Vendeur',)]
    try:
        cursor.executemany("INSERT INTO roles (name) VALUES (%s)", roles)
        print("  - Rôles insérés.")
    except Error as e:
        if e.errno == 1062: # Duplicate entry
            print("  - Les rôles semblent déjà exister.")
        else:
            print(f"ERREUR lors de l'insertion des rôles: {e}")
            raise

    # --- Utilisateur Admin ---
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if cursor.fetchone():
        print("  - L'utilisateur 'admin' existe déjà.")
        return

    print("\n--- Création de l'utilisateur 'admin' ---")
    admin_password = getpass.getpass("  - Veuillez choisir un mot de passe pour l'utilisateur 'admin': ")
    hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt())

    cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
    admin_role_id = cursor.fetchone()
    if not admin_role_id:
        print("ERREUR: Le rôle 'Admin' n'a pas été trouvé.")
        return

    admin_user = ('admin', hashed_password.decode('utf-8'), 'Administrateur Système', admin_role_id[0])
    cursor.execute(
        "INSERT INTO users (username, password_hash, full_name, role_id) VALUES (%s, %s, %s, %s)",
        admin_user
    )
    print("  - Utilisateur 'admin' créé avec succès.")


def seed_permissions(cursor):
    """Insère les permissions de base et les assigne aux rôles."""
    print("\nInsertion et assignation des permissions...")

    PERMISSIONS = [
        'dashboard.view',
        'commandes.view', 'commandes.create', 'commandes.edit', 'commandes.delete',
        'invoices.view', 'invoices.create', 'invoices.edit', 'invoices.delete',
        'clients.view', 'clients.create', 'clients.edit', 'clients.delete',
        'products.view', 'products.create', 'products.edit', 'products.delete',
        'reports.view',
        'settings.view', 'settings.users.manage', 'settings.roles.manage'
    ]

    # Insert permissions
    try:
        cursor.executemany("INSERT INTO permissions (name) VALUES (%s)", [(p,) for p in PERMISSIONS])
        print("  - Permissions de base insérées.")
    except Error as e:
        if e.errno == 1062: # Duplicate entry
            print("  - Les permissions semblent déjà exister.")
        else:
            raise

    # Define role-permission mapping
    ROLE_PERMISSIONS = {
        'Comptable': [
            'dashboard.view',
            'commandes.view', 'commandes.create', 'commandes.edit', 'commandes.delete',
            'invoices.view', 'invoices.create', 'invoices.edit',
            'clients.view', 'clients.create', 'clients.edit',
            'products.view', 'products.create', 'products.edit',
            'reports.view'
        ],
        'Vendeur': [
            'commandes.view', 'commandes.create',
            'invoices.view', 'invoices.create',
            'clients.view', 'clients.create', 'clients.edit',
            'products.view'
        ]
    }

    # Assign permissions to roles
    for role_name, permissions in ROLE_PERMISSIONS.items():
        try:
            cursor.execute("SELECT id FROM roles WHERE name = %s", (role_name,))
            role_id_result = cursor.fetchone()
            if not role_id_result:
                continue
            role_id = role_id_result[0]

            # Clear existing permissions for this role to ensure a clean slate
            cursor.execute("DELETE FROM role_permissions WHERE role_id = %s", (role_id,))

            placeholders = ', '.join(['%s'] * len(permissions))
            cursor.execute(f"SELECT id FROM permissions WHERE name IN ({placeholders})", permissions)
            permission_ids = [item[0] for item in cursor.fetchall()]

            role_perm_data = [(role_id, perm_id) for perm_id in permission_ids]
            cursor.executemany("INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)", role_perm_data)
            print(f"  - {len(permission_ids)} permissions assignées au rôle '{role_name}'.")

        except Error as e:
            print(f"ERREUR lors de l'assignation des permissions pour '{role_name}': {e}")
            raise

    # Admin gets all permissions
    try:
        cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
        admin_role_id_result = cursor.fetchone()
        if admin_role_id_result:
            admin_role_id = admin_role_id_result[0]
            cursor.execute("DELETE FROM role_permissions WHERE role_id = %s", (admin_role_id,))
            cursor.execute("SELECT id FROM permissions")
            all_permission_ids = [item[0] for item in cursor.fetchall()]
            admin_perm_data = [(admin_role_id, perm_id) for perm_id in all_permission_ids]
            cursor.executemany("INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)", admin_perm_data)
            print(f"  - Toutes les {len(all_permission_ids)} permissions assignées au rôle 'Admin'.")
    except Error as e:
        print(f"ERREUR lors de l'assignation des permissions pour 'Admin': {e}")
        raise


def insert_default_company(cursor):
    """Insère les informations de l'entreprise par défaut si la table est vide."""
    print("\nVérification des informations de l'entreprise...")
    cursor.execute("SELECT id FROM company_info LIMIT 1")
    if cursor.fetchone():
        print("  - Les informations de l'entreprise existent déjà.")
        return

    print("  - Aucune information d'entreprise trouvée, insertion des données par défaut...")
    company_data = (
        "SOCIETE GENERALE D'INDUSTRIES EN COTE D'IVOIRE",
        "225, Z.I, Abidjan, Côte d'Ivoire",
        "+225 0102030405",
        "contact@monentreprise.ci",
        "CI-XXX-1234567-X",
        "Sogici",
        "j33NYEEKXzXxSL88nXiqM8yWRSkO7hJv"
    )
    query = """
        INSERT INTO company_info (name, address, phone, email, ncc, point_of_sale, fne_api_key)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(query, company_data)
        print("  - Informations de l'entreprise par défaut insérées avec succès.")
    except Error as e:
        print(f"ERREUR lors de l'insertion des informations de l'entreprise: {e}")
        raise


def main():
    """Fonction principale pour exécuter le script (modifiée pour non-interactif)."""
    try:
        db_host = "127.0.0.1"
        db_user = "root"
        db_password = "Admin@1234"
        db_name = "s_facture_plus"

        # Connexion au serveur MySQL
        cnx = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password
        )
        cursor = cnx.cursor()

        # Création de la base de données
        create_database(cursor, db_name)

        # Sélection de la base de données
        cursor.execute(f"USE {db_name}")

        # Création des tables et insertion des données
        create_tables(cursor)
        insert_initial_data(cursor)
        seed_permissions(cursor)
        insert_default_company(cursor)
        # Pour l'admin, on ne peut pas utiliser getpass, donc on met un mot de passe par défaut "admin"
        print("\n--- Création de l'utilisateur 'admin' avec mot de passe 'admin' ---")
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            hashed_password = bcrypt.hashpw(b'admin', bcrypt.gensalt())
            cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
            admin_role_id_result = cursor.fetchone()
            if admin_role_id_result:
                admin_role_id = admin_role_id_result[0]
                admin_user = ('admin', hashed_password.decode('utf-8'), 'Administrateur Système', admin_role_id)
                cursor.execute(
                    "INSERT INTO users (username, password_hash, full_name, role_id) VALUES (%s, %s, %s, %s)",
                    admin_user
                )
                print("  - Utilisateur 'admin' créé avec succès.")
        else:
            print("  - L'utilisateur 'admin' existe déjà.")

        cnx.commit()
        print("\nConfiguration de la base de données terminée avec succès !")

    except Error as e:
        print(f"\nUne erreur est survenue: {e}")
    finally:
        if 'cnx' in locals() and cnx.is_connected():
            cursor.close()
            cnx.close()
            print("Connexion MySQL fermée.")

if __name__ == '__main__':
    main()
