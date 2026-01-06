# Script de génération de l'exécutable pour Windows (facturation_ci)
# Ce script doit être lancé depuis la racine du projet via PowerShell.

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "    Génération de l'exécutable S Facture + (v2)" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# 1. Vérification de l'installation de PyInstaller
if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Host "[INFO] PyInstaller n'est pas trouvé. Tentative d'installation..." -ForegroundColor Yellow
    try {
        pip install pyinstaller
    } catch {
        Write-Host "[ERREUR] Impossible d'installer PyInstaller. Vérifiez votre installation Python." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[OK] PyInstaller est installé." -ForegroundColor Green
}

# 2. Nettoyage des dossiers de build précédents
Write-Host "[INFO] Nettoyage des anciens fichiers de build..." -ForegroundColor Yellow
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }

# 3. Configuration des chemins
$EntryPoint = "facturation_ci/main.py"
$TemplatesSrc = "facturation_ci/templates"
$ImagesSrc = "facturation_ci/images"
# Chemin vers les navigateurs téléchargés localement
$BrowsersSrc = "browsers" 

# Chemin spécifique de l'icône demandé
$IconPath = "images/icon.ico"

# Vérification du fichier d'entrée
if (-not (Test-Path $EntryPoint)) {
    Write-Host "[ERREUR] Le fichier d'entrée $EntryPoint est introuvable." -ForegroundColor Red
    exit 1
}

# Vérification de l'icône
if (-not (Test-Path $IconPath)) {
    Write-Host "[AVERTISSEMENT] L'icône spécifiée '$IconPath' est introuvable." -ForegroundColor Yellow
    # Tentative de repli sur le dossier images interne
    if (Test-Path "facturation_ci/images/icon.ico") {
        $IconPath = "facturation_ci/images/icon.ico"
        Write-Host "[INFO] Utilisation de l'icône de secours : $IconPath" -ForegroundColor Gray
    } else {
        $IconPath = ""
        Write-Host "[INFO] Aucune icône ne sera utilisée pour l'exécutable." -ForegroundColor Gray
    }
} else {
    Write-Host "[OK] Icône trouvée : $IconPath" -ForegroundColor Green
}

# --- VÉRIFICATION CRITIQUE POUR PLAYWRIGHT ---
if (-not (Test-Path $BrowsersSrc)) {
    Write-Host "`n[ATTENTION] Le dossier '$BrowsersSrc' est introuvable !" -ForegroundColor Red
    Write-Host "Playwright ne fonctionnera pas dans l'exe." -ForegroundColor Yellow
    Write-Host "Veuillez exécuter ces commandes avant de lancer le build :" -ForegroundColor White
    Write-Host "  `$env:PLAYWRIGHT_BROWSERS_PATH = `"`$PWD\browsers`"" -ForegroundColor Gray
    Write-Host "  playwright install chromium" -ForegroundColor Gray
    Write-Host "Puis relancez ce script."
    exit 1
}
# ---------------------------------------------

# 4. Construction de la commande PyInstaller
Write-Host "[INFO] Lancement de PyInstaller..." -ForegroundColor Cyan

# Construction de la liste des arguments
$PyInstallerArgs = @(
    "--noconfirm",
    "--onedir",
    "--windowed",
    "--clean",
    "--name", "S Facture +",
    "--add-data", "$($TemplatesSrc + ';templates')",
    "--add-data", "$($ImagesSrc + ';images')",
    "--add-data", "$($BrowsersSrc + ';playwright/driver/package/.local-browsers')",
    "--hidden-import", "mysql.connector",
    "--hidden-import", "babel.numbers",
    "--collect-all", "playwright"
)

# Ajout de l'icône si elle est définie
if ($IconPath -ne "") {
    $PyInstallerArgs += "--icon"
    $PyInstallerArgs += $IconPath
}

$PyInstallerArgs += "$EntryPoint"

Write-Host "Arguments: $PyInstallerArgs" -ForegroundColor Gray

# Exécution de PyInstaller
& pyinstaller $PyInstallerArgs

# 5. Vérification du résultat
if ($LASTEXITCODE -eq 0) {
    Write-Host "`n==================================================" -ForegroundColor Green
    Write-Host "    SUCCÈS ! L'exécutable a été généré." -ForegroundColor Green
    Write-Host "==================================================" -ForegroundColor Green
    Write-Host "Emplacement : dist/S Facture +/S Facture +.exe" -ForegroundColor White
} else {
    Write-Host "`n==================================================" -ForegroundColor Red
    Write-Host "    ÉCHEC de la génération." -ForegroundColor Red
    Write-Host "==================================================" -ForegroundColor Red
}