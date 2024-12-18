import requests
from bs4 import BeautifulSoup

# L'URL mise à jour
url = 'https://www.save70.com/flights/?lang=fr&campaignid=20768486835&adgroupid=156036211576&lpage=skys&lb=k&gad_source=1&gclid=Cj0KCQiAgdC6BhCgARIsAPWNWH3OFb1X0etd52ZxrYCq-1DjnNsG7cmfJyV5ASWjRHVmIUNLTAAVuHQaAsvPEALw_wcB'

# Envoi de la requête GET pour récupérer le contenu de la page
response = requests.get(url)

# Vérification de la validité de la réponse
if response.status_code == 200:
    # Parser le contenu HTML de la page
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Exemples d'extraction de données spécifiques (à adapter selon la structure HTML)
    prix = soup.find_all('span', class_='price')  # Exemple : rechercher tous les éléments span avec la classe "price"
    for p in prix:
        print(p.text)  # Affiche les prix trouvés
    
    # Vous pouvez ajouter d'autres extractions selon la structure HTML du site
else:
    print(f"Erreur lors de la récupération de la page : {response.status_code}")
print("FIN")
