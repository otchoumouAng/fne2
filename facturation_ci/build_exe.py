import PyInstaller.__main__
import os

def create_executable():
    # Nom du script source
    script_name = "setup_database.py"
    
    # Nom de l'exécutable final souhaité
    exe_name = "Installateur_BDD_S_Facture_Plus"

    # Vérification de la présence du fichier source
    if not os.path.exists(script_name):
        print(f"Erreur : Le fichier {script_name} est introuvable dans ce dossier.")
        return

    print("--- Démarrage de la création de l'exécutable ---")
    
    try:
        PyInstaller.__main__.run([
            script_name,                      # Le fichier script principal
            f'--name={exe_name}',             # Nom de l'exe final
            '--onefile',                      # Créer un seul fichier .exe (pas de dossier de dépendances)
            '--console',                      # Garder la fenêtre noire (console) pour voir les logs
            '--clean',                        # Nettoyer le cache avant la construction
            '--icon=icone.ico',               # Fichier .ico
        ])
        
        print("\n" + "="*50)
        print("SUCCÈS ! L'exécutable a été généré.")
        print(f"Vous le trouverez dans le dossier : dist/{exe_name}.exe")
        print("="*50)
        
    except Exception as e:
        print(f"Une erreur est survenue lors de la compilation : {e}")

if __name__ == "__main__":
    create_executable()