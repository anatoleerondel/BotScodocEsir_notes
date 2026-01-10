import os
import sys
import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager

# --- RÉCUPÉRATION DES SECRETS ---
TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
USER = os.environ["USER_ESIR"]
PASS = os.environ["PASS_ESIR"]
URL_TARGET = "https://scodoc-notes.esir.univ-rennes1.fr/"

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except:
        pass

def check_grades():
    print("Configuration de Firefox Headless...")
    options = Options()
    options.add_argument("--headless") # Obligatoire : pas d'écran sur le serveur
    
    service = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        driver.get(URL_TARGET)
        time.sleep(5) # Attente chargement initial
        
        # --- LOGIQUE DE CONNEXION (Méthode Brute) ---
        if len(driver.find_elements(By.ID, "username")) > 0:
            print("Connexion en cours...")
            driver.find_element(By.ID, "username").send_keys(USER)
            driver.find_element(By.ID, "password").send_keys(PASS)
            
            # Validation
            if len(driver.find_elements(By.NAME, "submit")) > 0:
                driver.find_element(By.NAME, "submit").click()
            elif len(driver.find_elements(By.CSS_SELECTOR, "button[type='submit']")) > 0:
                driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
                
            print("Identifiants envoyés. Attente 15s...")
            time.sleep(15) 
        
        # --- COMPTAGE (Méthode Regex Note + Coef) ---
        full_text = driver.find_element(By.TAG_NAME, "body").text
        
        # 1. Notes avec "Coef" à côté
        trouvailles = re.findall(r'(\d{1,2}\.\d{2})\s+Coef', full_text)
        # 2. Notes seules sur une ligne
        pattern_notes_seules = re.findall(r'\n\s*(\d{1,2}\.\d{2})\s*\n', full_text)
        
        # Total
        toutes_les_notes = trouvailles + pattern_notes_seules
        count = len(toutes_les_notes)
        
        print(f"Notes trouvées : {count}")
        return count

    except Exception as e:
        print(f"Erreur : {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    # Lecture de l'ancien nombre
    last_count = 0
    file_path = "last_count.txt"
    
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            try:
                last_count = int(f.read().strip())
            except:
                last_count = 0
    
    # Lancement de la vérification
    current = check_grades()
    
    if current is not None:
        if current > last_count:
            diff = current - last_count
            # Message personnalisé
            msg = f"🔔 NOUVELLE NOTE ! Tu as {diff} nouvelle(s) note(s). (Total : {current})"
            print(msg)
            send_telegram(msg)
            
            # Sauvegarde
            with open(file_path, "w") as f:
                f.write(str(current))
                
        elif current < last_count:
            # Mise à jour silencieuse si note supprimée
            with open(file_path, "w") as f:
                f.write(str(current))
        else:
            print("Rien de nouveau.")
