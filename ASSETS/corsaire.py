import tkinter as tk
from PIL import Image, ImageTk
import os
import requests
import subprocess
import sys

# EXPECTED = os.path.expanduser("~/Desktop/Duel_en_Haute_Mer")
# if not os.path.abspath(__file__).startswith(EXPECTED):
#     raise Exception(f"MAUVAIS DOSSIER : {__file__}")
print(">>> RUNNING :", __file__)
print(">>> CLIENT UTILISÉ :", __file__)

base_dir = os.path.dirname(__file__)
pirate_path = os.path.join(base_dir, "pirate.py")

MODE_PIRATE_HUMAIN = False

pirate_path = os.path.join(base_dir, "pirate.py")

if MODE_PIRATE_HUMAIN and os.path.exists(pirate_path):
    subprocess.Popen([sys.executable, pirate_path])
else:
    print("pirate.py introuvable :", pirate_path)
player_S = {"game_over": False}

# ---------------------------------------------------------
# CONNEXION AU SERVEUR
# ---------------------------------------------------------

PORT_SERVEUR = 5050
BASE_URL = f"http://127.0.0.1:{PORT_SERVEUR}"

print("Serveur utilisé :", BASE_URL)


# === CONFIGURATION DYNAMIQUE ===
joueur = "corsaire"   # dans pirate.py : "pirate"

last_horn = ""

ADVERSAIRE = {
    "corsaire": "pirate",
    "pirate": "corsaire"
}

adversaire = ADVERSAIRE[joueur]

# ---------------------------------------------------------
# MODES
MODE_DEPLACEMENT_CLIC = True 
MAX_MOVE = 1
DELAI_MESSAGES = 300      # rafraîchissement serveur
DELAI_ACTION = 300          # délai visuel (optionnel)
# ---------------------------------------------------------

global corsaire_doit_reculer

def faire_reculer_corsaire(source_type):
    if source_type == "territoire":
        print("RECUL ANNULÉ : tir depuis territoire")
        return

    print(">>> FAIRE RECULER CORSAIRE APPELÉ <<<")

    try:
        etat = requests.get(f"{BASE_URL}/etat", timeout=1).json()

        row, col = etat["state"]["corsaire"]["pos"]
        row_a, col_a = etat["state"]["pirate"]["pos"]

        new_row = row
        new_col = col

        if row_a > row:
            new_row -= 1
        elif row_a < row:
            new_row += 1

        if col_a > col:
            new_col -= 1
        elif col_a < col:
            new_col += 1

        print("RECUL CORSAIRE :", (row, col), "->", (new_row, new_col))

        if 0 <= new_row < GRID_ROWS and 0 <= new_col < GRID_COLS:
            ok = envoyer_move("corsaire", new_row, new_col)
            print("RECUL OK =", ok)

            if ok:
                root.after(DELAI_ACTION, lambda: replacer_bateau(new_row, new_col))

    except Exception as e:
        print("ERREUR RECUL CORSAIRE :", e)
def annoncer_presence():
    import requests
    try:
        r = requests.post(f"{BASE_URL}/ready", json={"joueur": joueur}, timeout=1)
    except Exception as e:
        print("ERREUR READY :", e)

# --- FEU D'ARTIFICE ---

fireworks_on = False

IMAGES_TERRITOIRES = {
    "L'île":   "Ter_Centre.png",
    "Ter_N_W": "Ter_N_W.png",
    "Ter_N_E": "Ter_N_E.png",
    "Ter_S_W": "Ter_S_W.png",
    "Ter_S_E": "Ter_S_E.png"
}

def afficher_tresor_ile(etat):
    nb_tresors = etat.get("tresor", {}).get("restants", 0)

    texte_tresor = "•" * nb_tresors

    row, col = 7, 10

    x = MARGE_LEFT + col * CELL_SIZE + CELL_SIZE / 2
    y = MARGE_TOP + row * CELL_SIZE + CELL_SIZE / 2

    canvas.delete("tresor_ile")

    # 🔴 NOUVEAU : masquer si Corsaire possède l'île
    owner_ile = etat.get("territoires", {}).get("L'île", {}).get("owner")
    if owner_ile == "corsaire":
        return

    for i in range(nb_tresors):
        dx = (i - nb_tresors / 2) * 10  # espacement

        # centre
        cx = x + dx
        cy = y

        # dimensions (moitié largeur, moitié hauteur)
        largeur = 2
        hauteur = 6

        x1 = cx - largeur
        y1 = cy - hauteur
        x2 = cx + largeur
        y2 = cy + hauteur

        canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="gold",
            outline="orange",
            width=1,
            tags="tresor_ile"
        )
        
def stop_feu_artifice():
    global fireworks_on
    fireworks_on = False
    canvas.delete("feu_artifice")

def lancer_feu_artifice(duree_ms=12000):
    global fireworks_on
    fireworks_on = True
    feu_artifice_step()
    root.after(duree_ms, stop_feu_artifice)

def feu_artifice_step():
    global fireworks_on

    if not fireworks_on:
        return

    import random

    centre_row = GRID_ROWS // 2
    centre_col = GRID_COLS // 2

    row = random.randint(max(0, centre_row - 2), min(GRID_ROWS - 1, centre_row + 2))
    col = random.randint(max(0, centre_col - 2), min(GRID_COLS - 1, centre_col + 2))

    x = (col + 1) * CELL_SIZE + CELL_SIZE // 2
    y = (row + 1) * CELL_SIZE + CELL_SIZE // 2

    impact_id = canvas.create_text(
        x, y,
        text="💥",
        font=("Arial", 24),
        tags="feu_artifice"
    )

    root.after(250, lambda: canvas.delete(impact_id))
    root.after(250, feu_artifice_step)
    
def effet_impact_case(row, col):
    x1 = (col + 1) * CELL_SIZE
    y1 = (row + 1) * CELL_SIZE
    x2 = x1 + CELL_SIZE
    y2 = y1 + CELL_SIZE

    flash = canvas.create_rectangle(
        x1, y1, x2, y2,
        fill="#aa0000", outline=""
    )

    anneau = canvas.create_oval(
        x1 + 4, y1 + 4, x2 - 4, y2 - 4,
        outline="orange", width=2
    )

    etat = {"visible": True}
    duree_totale = 3000
    temps = 0

    def clignoter():
        nonlocal temps

        if temps >= duree_totale:
            canvas.delete(flash)
            canvas.delete(anneau)
            return

        # alternance visible / caché
        if etat["visible"]:
            canvas.itemconfigure(flash, state="hidden")
            canvas.itemconfigure(anneau, state="hidden")
        else:
            canvas.itemconfigure(flash, state="normal")
            canvas.itemconfigure(anneau, state="normal")

        etat["visible"] = not etat["visible"]

        # ⏱️ vitesse qui ralentit progressivement
        intervalle = 80 + int((temps / duree_totale) * 400)
        # → débute ~80 ms (rapide)
        # → finit ~480 ms (lent)

        temps += intervalle
        root.after(intervalle, clignoter)

    clignoter()
        
def afficher_hits_restants():
    canvas.delete("texte_territoire")
    canvas.delete("texte_port")
    try:
        etat = requests.get(f"{BASE_URL}/etat", timeout=1).json()
        bateaux_restants = etat["bateaux_restants"]
        territoires_restants = etat["territoires_restants"]
        territoires = etat["territoires"]

        canvas.delete("texte_territoire")

        # --- bateaux corsaire en B8 ---
        restants_corsaire = bateaux_restants["corsaire"]
        tirs_corsaire = etat["state"]["corsaire"]["shots_left"]
        
        row_c, col_c = 7, 1
        x_c = MARGE_LEFT + col_c * CELL_SIZE + CELL_SIZE - 4
        y_c = MARGE_TOP + row_c * CELL_SIZE + CELL_SIZE // 2

        canvas.create_text(
            x_c, y_c,
            text=f"{restants_corsaire}\n{tirs_corsaire}",
            fill="white",
            font=("Arial", 13, ""),
            anchor="e",
            justify="right",
            tags="texte_port"
        )

        # --- bateaux pirate en T8 ---
        restants_pirate = bateaux_restants["pirate"]
        tirs_pirate = etat["state"]["pirate"]["shots_left"]

        row_p, col_p = 7, 19
        x_p = MARGE_LEFT + col_p * CELL_SIZE + 4
        y_p = MARGE_TOP + row_p * CELL_SIZE + CELL_SIZE // 2

        canvas.create_text(
            x_p, y_p,
            text=f"{restants_pirate}\n{tirs_pirate}",
            fill="white",
            font=("Arial", 13, ""),
            anchor="w",
            justify="left",
            tags="texte_port"
        )

        # --- territoires ---
        for nom, infos in territoires.items():
            if nom == "L'île":
                continue

            row, col = infos["coord"]
            resistance = territoires_restants[nom]

            x = (col + 1) * CELL_SIZE + CELL_SIZE // 2

            if row < GRID_ROWS // 2:
                y = row * CELL_SIZE + 5
            else:
                y = (row + 2) * CELL_SIZE + CELL_SIZE - 30

            canvas.create_text(
                x, y,
                text=f"{resistance}",
                fill="white",
                font=("Arial", 9, "bold"),
                anchor="n",
                justify="center",
                tags="texte_territoire"
            )

        # 🔴 Gestion des couches
        canvas.tag_raise("texte_territoire")
        canvas.tag_raise("texte_port")
        canvas.tag_raise("bateau")

    except Exception as e:
        print("ERREUR hits/territoires :", e)
        
def enlever_pavillon(nom_territoire):
    canvas.delete("pavillon")
    reafficher_pavillons_depuis_serveur()

def afficher_impact(case):
    row, col = case

    x = MARGE_LEFT + col * CELL_SIZE + CELL_SIZE // 2
    y = MARGE_TOP + row * CELL_SIZE + CELL_SIZE // 2

    impact_id = canvas.create_text(
        x, y,
        text="💥",
        font=("Arial", 18)
    )

    root.after(200, lambda i=impact_id: canvas.delete(i))
    
def afficher_signal(row, col):
    canvas.delete("signal_temp")

    x = (col + 1) * CELL_SIZE + CELL_SIZE // 2
    y = (row + 1) * CELL_SIZE + CELL_SIZE // 2

    signal_id = canvas.create_image(
        x, y,
        image=canvas.signal_pirate_img,
        tags="signal_temp"
    )

    canvas.tag_raise(signal_id)

    root.after(1200, lambda: canvas.delete(signal_id))
    
def jouer_explosion_forte():
    chemin = os.path.join(base_dir, "ASSETS", "expl.wav")

    if os.path.exists(chemin):
        subprocess.Popen(
            ["afplay", "-v", "1.0", chemin],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        print("FICHIER EXPLOSION INTROUVABLE :", chemin)
            
def jouer_explosion_faible():
    chemin = os.path.join(base_dir, "ASSETS", "expl_faible.wav")
    print("PLAY EXPLOSION FAIBLE =", chemin)

    if os.path.exists(chemin):
        subprocess.Popen(
            ["afplay", "-v", "0.35", chemin],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
      
def jouer_son(nom_fichier, volume="1.0"):
    chemin = os.path.join(base_dir, "ASSETS", nom_fichier)

    if os.path.exists(chemin):
        subprocess.Popen(
            ["afplay", "-v", volume, chemin],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        print("FICHIER SON INTROUVABLE :", chemin)
        
def afficher_pavillon(nom_territoire, owner):
    try:
        etat = requests.get(f"{BASE_URL}/etat", timeout=1).json()
        territoires = etat["territoires"]

        if nom_territoire not in territoires:
            return

        row, col = territoires[nom_territoire]["coord"]

        x = MARGE_LEFT + col * CELL_SIZE
        y = MARGE_TOP + row * CELL_SIZE

        canvas.delete(f"pavillon_{nom_territoire}")

        if owner == "corsaire":
            image = pavillon_corsaire_img
        elif owner == "pirate":
            image = pavillon_pirate_img
        else:
            return

        canvas.create_image(
            x, y,
            anchor="nw",
            image=image,
            tags=(f"pavillon_{nom_territoire}", "pavillon")
        )

        # remettre le bateau au-dessus
        canvas.tag_raise("impact")
        canvas.tag_raise("bateau")

    except Exception as e:
        print("ERREUR afficher_pavillon :", e)

from ocean import (
    creer_ocean,
    WIDTH, HEIGHT,
    CELL_SIZE, MARGE_LEFT, MARGE_TOP,
    PORTS, GRID_ROWS, GRID_COLS, TERRITOIRES
)

def case_vers_pixels(row, col):
    x = MARGE_LEFT + col * CELL_SIZE
    y = MARGE_TOP + row * CELL_SIZE
    return x, y

def pixels_vers_case(x, y):
    col = round((x - MARGE_LEFT) / CELL_SIZE)
    row = round((y - MARGE_TOP) / CELL_SIZE)
    return row, col

def jouer_horn():
    chemin = os.path.join(base_dir, "ASSETS", "horn.wav")
    print("PLAY HORN =", chemin)

    if os.path.exists(chemin):
        subprocess.Popen(["afplay", chemin])
    else:
        print("FICHIER HORN INTROUVABLE :", chemin)

IMAGES_BATEAUX = {
    "corsaire": "corsaire.png",
    "pirate": "pirate.png"
}
  
# --- FONCTIONS SERVEUR ---
def get_position_depuis_serveur(joueur):
    try:
        r = requests.get(f"{BASE_URL}/etat", timeout=1)
        data = r.json()
        return data["state"][joueur]["pos"]
    except Exception as e:
        print("⚠️ serveur non joignable :", e)
        return None
        
def reafficher_pavillons_depuis_serveur():
    try:
        r = requests.get(f"{BASE_URL}/etat", timeout=1)
        data = r.json()
        territoires = data.get("territoires", {})

        canvas.delete("pavillon")

        for nom_territoire, infos in territoires.items():
            owner = infos.get("owner", "")
            if owner:
                afficher_pavillon(nom_territoire, owner)

    except Exception as e:
        print("ERREUR REAFFICHAGE PAVILLONS :", e)        

def envoyer_move(joueur, row, col):
    try:
        r = requests.post(
            f"{BASE_URL}/move",
            json={"joueur": joueur, "row": row, "col": col},
            timeout=1
        )

        print("STATUS /move =", r.status_code)
        print("TEXTE /move =", r.text)

        if not r.text.strip():
            return False

        data = r.json()
        print("REPONSE /move =", data)

        return data.get("ok", False)

    except Exception as e:
        print("⚠️ erreur envoi move :", e)
        return False

def traiter_horn(emetteur):
    jouer_horn()
    faire_clignoter_port(emetteur)

def watch_messages():

    try:
        r = requests.get(f"{BASE_URL}/messages/{joueur}", timeout=1)
        msgs = r.json().get("messages", [])

        if msgs:
            requests.post(f"{BASE_URL}/reset/{joueur}", timeout=1)

        for m in msgs:

            if m == "#QUIT":
                print(">>> QUIT RECU : fermeture Corsaire")
                root.quit()
                root.destroy()
                sys.exit(0)

            if not m.startswith("#SIGNAL:"):
                print("MSG RECU :", m)

            if m.startswith("#ENDGAME:"):
                player_S["game_over"] = True

                _, vainqueur = m.split(":")

                if vainqueur == "corsaire":
                    nom_vainqueur = "Surcouf"
                else:
                    nom_vainqueur = "Barbe Noire"

                show_endgame_banner(f"🏆 Mer belle! {nom_vainqueur} maître des océans")

            elif m.startswith("#HORN:"):
                if not player_S["game_over"]:
                    _, emetteur = m.split(":")
                    if emetteur != joueur or joueur == "corsaire":
                        traiter_horn(emetteur)
                        
            elif m.startswith("#FLAG:"):
                _, nom_territoire, owner = m.split(":", 2)

                if not owner:
                    enlever_pavillon(nom_territoire)
                else:
                    afficher_pavillon(nom_territoire, owner)

            elif m == "#RESETGAME":
                player_S["game_over"] = False

                stop_endgame_banner()
                stop_feu_artifice()

                # --- RECHARGER ETAT COMPLET ---
                etat = requests.get(f"{BASE_URL}/etat", timeout=1).json()

                # --- RECREER OCEAN COMPLET ---
                creer_ocean(canvas, etat["territoires"], etat["rochers"], etat)

                # --- REPLACER BATEAU ---
                pos = etat["state"][joueur]["pos"]
                root.after(DELAI_ACTION, lambda: replacer_bateau(pos[0], pos[1]))

                # --- RAFRAICHIR TOUT ---
                reafficher_pavillons_depuis_serveur()
                afficher_hits_restants()
                afficher_tresor_ile(etat)
                
            elif m == "##INFO_ARMURIER:2":
                show_info_banner("Message de l'armurier : plus que 2 boulets à tirer")

            elif m == "##INFO_ARMURIER:1":
                show_info_banner("Message de l'armurier : Dernier tir restant")

            elif m == "##INFO_ARMURIER:0":
                show_info_banner("Message de l'armurier : Plus de tirs pour ce bateau — retour au port")
                
            elif m.startswith("#READY:"):
                _, joueur_pret = m.split(":")
                if joueur_pret != joueur:
                    faire_clignoter_port(joueur_pret)
                    
            elif m.startswith("#TIR:"):
                _, tireur, resultat, case_txt = m.split(":")
                row, col = map(int, case_txt.split(","))

                afficher_impact((row, col))

                # 👉 son du tireur (ajouté, sans toucher au reste)
                if tireur == "corsaire":
                    subprocess.Popen(
                        ["afplay", "-v", "1.0", os.path.join(base_dir, "ASSETS", "Tir.wav")],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                elif tireur == "pirate":
                    subprocess.Popen(
                        ["afplay", "-v", "0.8", os.path.join(base_dir, "ASSETS", "Tir.wav")],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )

                # 👉 logique d'origine inchangée
                if resultat == "manque":
                    jouer_explosion_faible()

                elif resultat == "touche":
                    jouer_explosion_forte()
                    lancer_feu_artifice()
                    effet_impact_case(row, col)

                    if not player_S["game_over"] and tireur != joueur:
                        pos = get_position_depuis_serveur(joueur)
                        if pos:
                            replacer_bateau(pos[0], pos[1])
                
            elif m.startswith("#SIGNAL:"):
                print("SIGNAL RECU BRUT :", m)

                try:
                    _, joueur_signal, coords = m.split(":")
                    row, col = map(int, coords.split(","))

                    afficher_signal(row, col)

                except Exception as e:
                    print("ERREUR SIGNAL :", e)

    except Exception as e:
        print("ERREUR watch_messages :", e)

    try:
        etat = requests.get(f"{BASE_URL}/etat", timeout=1).json()
        afficher_tresor_ile(etat)
    except Exception as e:
        print("ERREUR affichage tresor :", e)

    afficher_hits_restants()
    root.after(DELAI_MESSAGES, watch_messages)
    
def on_right_click(event):
    print(">>> ON_RIGHT_CLICK DIRECT APPELÉ <<<")
    
    # clic droit direct = tir vers la case cliquée
    if event.x < MARGE_LEFT or event.y < MARGE_TOP:
        return

    col = (event.x - MARGE_LEFT) // CELL_SIZE
    row = (event.y - MARGE_TOP) // CELL_SIZE

    if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
        print("TIR HORS GRILLE")
        return

    position = [row, col]

    try:
        r = requests.post(
            f"{BASE_URL}/tir",
            json={
                "joueur": joueur,
                "source": None,      # le serveur choisira la source
                "position": position
            },
            timeout=1
        )

        data = r.json()
        print("TIR DIRECT ENVOYÉ =", joueur, position, data)
        
        if data.get("ok"):
            pos = get_position_depuis_serveur(joueur)
            if pos:
                replacer_bateau(pos[0], pos[1])
                
        if not data.get("ok"):
            print("TIR REFUSÉ :", data.get("message"))

            if data.get("resultat") == "refuse":
                show_info_banner(data.get("message", "Tir refusé"))

        else:
            resultat = data.get("resultat")

            if joueur == "corsaire" and data.get("source_type") == "bateau":
                print(">>> RECUL CORSAIRE PROGRAMMÉ <<<")
                #root.after(500, lambda: faire_reculer_corsaire("bateau"))

            if resultat == "manqué":
                print(">>> MANQUÉ <<<")

            elif resultat == "touché":
                print(">>> TOUCHÉ <<<")
    except Exception as e:
        print("ERREUR TIR DIRECT :", e)
            
def on_left_click_fire(event):
    if event.x < MARGE_LEFT or event.y < MARGE_TOP:
        return

    col = (event.x - MARGE_LEFT) // CELL_SIZE
    row = (event.y - MARGE_TOP) // CELL_SIZE

    if not (0 <= row < GRID_ROWS and 0 <= col < GRID_COLS):
        print("DEPLACEMENT HORS GRILLE")
        return

    print("DEPLACEMENT DEMANDÉ =", row, col)

    try:
        ok = envoyer_move(joueur, row, col)

        if ok:
            replacer_bateau(row, col)
        else:
            pos = get_position_depuis_serveur(joueur)
            if pos:
                replacer_bateau(pos[0], pos[1])

    except Exception as e:
        print("ERREUR MOVE CLIC :", e)
 
root = tk.Tk()
root.geometry("+250+50")
root.title("Mer des Caraïbes")

root.after(500, lambda: (
    root.lift(),
    root.focus_force()
))

canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT)
canvas.pack()

etat = requests.get(f"{BASE_URL}/etat", timeout=1).json()
creer_ocean(canvas, etat["territoires"], etat["rochers"], etat)

pavillon_corsaire_img = ImageTk.PhotoImage(
    Image.open(os.path.join(base_dir, "ASSETS", "pavillon_corsaire.png")).resize((CELL_SIZE, CELL_SIZE))
)

pavillon_pirate_img = ImageTk.PhotoImage(
    Image.open(os.path.join(base_dir, "ASSETS", "pavillon_pirate.png")).resize((CELL_SIZE, CELL_SIZE))
)

# --- BATEAU ---
base_dir = os.path.dirname(__file__)
chemin_bateau = os.path.join(base_dir, "ASSETS", IMAGES_BATEAUX[joueur])
img = Image.open(chemin_bateau).resize((CELL_SIZE, CELL_SIZE))
bateau_img = ImageTk.PhotoImage(img)
canvas.bateau_img = bateau_img

pos = get_position_depuis_serveur(joueur)
if pos:
    row, col = pos
else:
    row, col = PORTS["pirate"]

x = MARGE_LEFT + col * CELL_SIZE
y = MARGE_TOP + row * CELL_SIZE

bateau_id = canvas.create_image(x, y, anchor="nw", image=bateau_img, tags="bateau")

# --- ÉTAT DRAG ---
drag_data = {
    "active": False,
    "start_row": row,
    "start_col": col,
    "offset_x": 0,
    "offset_y": 0,
}


def case_vers_pixels(row, col):
    x = MARGE_LEFT + col * CELL_SIZE
    y = MARGE_TOP + row * CELL_SIZE
    return x, y

def pixels_vers_case(x, y):
    col = round((x - MARGE_LEFT) / CELL_SIZE)
    row = round((y - MARGE_TOP) / CELL_SIZE)
    return row, col

def replacer_bateau(row, col):
    x, y = case_vers_pixels(row, col)
    canvas.coords(bateau_id, x, y)
        
canvas.bind("<Button-2>", on_right_click)   # Mac clic droit
canvas.bind("<Button-1>", on_left_click_fire)     # clic gauche = déplacement ou action futur
canvas.bind("<Button-3>", on_right_click)
canvas.bind("<Control-Button-1>", on_right_click)

# === CONFIGURATION FIN DE PARTIE ===

endgame_banner = None
endgame_flash = False


def stop_info_banner():
    global info_banner

    if info_banner:
        info_banner.destroy()
        info_banner = None

def show_endgame_banner(message):
    global endgame_banner, endgame_flash

    if endgame_banner:
        endgame_banner.destroy()

    endgame_banner = tk.Label(
        root,
        text=message,
        font=("Arial", 18, "bold"),
        fg="white",
        bg="red",
        padx=20,
        pady=10
    )
    endgame_banner.place(relx=0, y=5 * CELL_SIZE, relwidth=1)

    endgame_flash = True
    clignoter_endgame()
    lancer_feu_artifice(60000)

    root.after(4000, stop_endgame_banner)   # ← 12 secondes

def clignoter_endgame():
    global endgame_flash

    if not endgame_flash:
        return

    current = endgame_banner.cget("bg")

    if current == "red":
        endgame_banner.config(bg="tomato")
    else:
        endgame_banner.config(bg="red")

    root.after(500, clignoter_endgame)
    
def stop_endgame_banner():
    global endgame_flash, endgame_banner

    endgame_flash = False

    if endgame_banner:
        endgame_banner.destroy()
        endgame_banner = None

# === CONFIGURATION BANDEAUX ===

info_banner = None
info_banner_token = 0


def show_info_banner(message):
    global info_banner, info_banner_token

    info_banner_token += 1
    mon_token = info_banner_token

    if info_banner is not None:
        try:
            info_banner.destroy()
        except Exception:
            pass
        info_banner = None

    info_banner = tk.Label(
        root,
        text=message,
        font=("Arial", 14, "bold"),
        fg="white",
        bg="red",
        padx=10,
        pady=5
    )
    info_banner.place(relx=0, rely=0, relwidth=1)

    def auto_close():
        global info_banner
        if mon_token == info_banner_token and info_banner is not None:
            try:
                info_banner.destroy()
            except Exception:
                pass
            info_banner = None

    root.after(3000, auto_close)


# ================================
# CLIGNOTEMENT PORT
# ================================

clignotement_port = False
port_clignotant = None


def stop_clignotement_port():
    global clignotement_port, port_clignotant
    clignotement_port = False
    port_clignotant = None
    canvas.delete("port_highlight")


def faire_clignoter_port(joueur_cible):
    global clignotement_port, port_clignotant

    clignotement_port = True
    port_clignotant = joueur_cible

    clignoter_port_step(True)

    root.after(8000, stop_clignotement_port)
    
def clignoter_port_step(visible):
    global clignotement_port, port_clignotant

    if not clignotement_port or port_clignotant is None:
        canvas.delete("port_highlight")
        return

    row, col = PORTS[port_clignotant]

    x1 = MARGE_LEFT + col * CELL_SIZE
    y1 = MARGE_TOP + row * CELL_SIZE
    x2 = x1 + CELL_SIZE
    y2 = y1 + CELL_SIZE

    canvas.delete("port_highlight")

    if visible:
        # 1) cercle extérieur
        marge = 8
        canvas.create_oval(
            x1 - marge, y1 - marge,
            x2 + marge, y2 + marge,
            outline="yellow",
            width=2,
            tags="port_highlight"
        )

        # 2) cercle case
        canvas.create_oval(
            x1, y1,
            x2, y2,
            outline="yellow",
            width=2,
            tags="port_highlight"
        )

        # 3) cercle demi-case centré
        demi = CELL_SIZE // 4
        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        canvas.create_oval(
            cx - demi, cy - demi,
            cx + demi, cy + demi,
            outline="yellow",
            width=2,
            tags="port_highlight"
        )

        canvas.tag_raise("port_highlight")
        canvas.tag_raise("bateau")

    root.after(500, lambda: clignoter_port_step(not visible))
# ================================
# DEMARRAGE
# ================================
reafficher_pavillons_depuis_serveur()
afficher_hits_restants()

annoncer_presence()
watch_messages()
root.mainloop()