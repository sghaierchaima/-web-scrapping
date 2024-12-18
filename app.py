import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
from io import BytesIO
from bson import Binary

# Configuration MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['product_db']
collection = db['products']

# Initialisation de WebDriver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Mode sans interface graphique
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# URLs des sites à scraper
sites = {
    "amazon": "https://www.amazon.com/s?k={query}&page={page}",
    "ebay": "https://www.ebay.fr/sch/i.html?_nkw={query}&_pgn={page}"
}

# Extraire les liens des produits
def get_product_links(driver, site, query, page_number):
    search_url = sites[site].format(query=query, page=page_number)
    driver.get(search_url)
    WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))

    product_links = []
    try:
        if site == "amazon":
            products = driver.find_elements(By.XPATH, "//a[contains(@class, 'a-link-normal s-no-outline')]")
        elif site == "ebay":
            products = driver.find_elements(By.XPATH, "//li[contains(@class, 's-item')]//a[@class='s-item__link']")

        for product in products:
            link = product.get_attribute('href')
            if link:
                product_links.append(link)
    except Exception as e:
        print(f"Erreur lors de l'extraction des liens ({site}, page {page_number}): {e}")
    return product_links

# Extraire les informations des produits
def extract_product_info(driver, site, product_url):
    try:
        driver.get(product_url)
        product_info = {"url": product_url, "site": site}  # Ajout du champ "site"

        if site == "amazon":
            try:
                product_info["product_name"] = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                ).text
            except Exception as e:
                product_info["product_name"] = "Nom non disponible"
                print(f"Erreur lors de l'extraction du titre ({product_url}): {e}")

            try:
                price = driver.find_element(By.XPATH, "//span[@class='a-price-whole']").text
                product_info["price"] = price
            except Exception as e:
                product_info["price"] = "Prix non disponible"
                print(f"Erreur lors de l'extraction du prix ({product_url}): {e}")

        elif site == "ebay":
            try:
                product_info["product_name"] = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//h1[@class='x-item-title__mainTitle']"))
                ).text
            except Exception as e:
                product_info["product_name"] = "Nom non disponible"
                print(f"Erreur lors de l'extraction du titre ({product_url}): {e}")

            try:
                price_section = driver.find_element(By.XPATH, "//div[@class='x-price-primary']")
                price = price_section.find_element(By.XPATH, ".//span[contains(@class, 'ux-textspans')]").text
                product_info["price"] = price
            except Exception as e:
                product_info["price"] = "Prix non disponible"
                print(f"Erreur lors de l'extraction du prix ({product_url}): {e}")

            try:
                image_element = driver.find_element(By.XPATH, "//img[@alt and contains(@data-zoom-src, 's-l')]")
                image_url = image_element.get_attribute('data-zoom-src')

                # Télécharger l'image
                image_response = requests.get(image_url)
                image_binary = Binary(image_response.content)
                product_info["image"] = image_binary
            except Exception as e:
                product_info["image"] = None
                print(f"Erreur lors de l'extraction de l'image ({product_url}): {e}")

        return product_info
    except Exception as e:
        print(f"Erreur lors de l'extraction des données ({product_url}): {e}")
        return None

# Sauvegarder dans MongoDB
def save_to_mongo(product_info):
    if product_info:
        try:
            collection.insert_one(product_info)
            print(f"Produit sauvegardé : {product_info['product_name']} | Site : {product_info['site']}")
        except Exception as e:
            print(f"Erreur MongoDB : {e}")

# Fonction principale
def main():
    driver = init_driver()
    search_queries = ["laptops"]  # Mots-clés de recherche

    try:
        for site in ["ebay", "amazon"]:  # eBay d'abord, puis Amazon
            for query in search_queries:
                print(f"Recherche pour '{query}' sur {site}...")
                for page in range(1, 3):  # Limité à 2 pages par requête
                    product_links = get_product_links(driver, site, query, page)
                    if not product_links:
                        break

                    for link in product_links:
                        print(f"Scraping produit : {link}")
                        product_info = extract_product_info(driver, site, link)
                        if product_info:
                            save_to_mongo(product_info)
    finally:
        driver.quit()
        print("Scraping terminé.")

if __name__ == "__main__":
    main()
