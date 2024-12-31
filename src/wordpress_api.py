import requests
from requests.auth import HTTPBasicAuth
from src.utils import ensure_tags_exist
import re
from PIL import Image
import io

def publish_to_wordpress(article, wordpress_url, username, password):
    """
    Publikuje artykuł na WordPressie za pomocą REST API.

    :param article: Słownik zawierający dane artykułu (title, slug, content).
    :param wordpress_url: URL strony WordPress (np. https://yourwebsite.com).
    :param username: Nazwa użytkownika WordPress z uprawnieniami do publikacji.
    :param password: Hasło lub token aplikacji użytkownika.
    :return: Odpowiedź API WordPress jako słownik lub None w przypadku błędu.
    """
    endpoint = f"{wordpress_url}/wp-json/wp/v2/posts"
    tag_ids = ensure_tags_exist(article["tags"], wordpress_url, username, password)

    # Dane artykułu
    payload = {
        "title": article["title"],
        "slug": article["slug"],
        "content": article["content"],
        "categories": article["categories"],  # "categories" musi być listą
        "tags": tag_ids,
        "status": "draft",
        "date": article["date"],
        "featured_media": article.get("featured_media")  # Jeśli chcemy od razu przypisać media
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            auth=HTTPBasicAuth(username, password)
        )

        if response.status_code == 201:  # 201 oznacza, że post został utworzony
            print(f"Artykuł '{article['title']}' został przesłany!")
            return response.json()
        else:
            print(f"Błąd podczas publikacji artykułu: {response.status_code}")
            print(response.json())
            return None

    except requests.RequestException as e:
        print(f"Błąd podczas połączenia z WordPress: {e}")
        return None


import requests
from requests.auth import HTTPBasicAuth
from PIL import Image
import io

def upload_image_to_wordpress(image_url, wordpress_url, username, password):
    """
    Pobiera obraz ze wskazanego URL, konwertuje go na PNG i przesyła do WordPress,
    zwracając ID przesłanego obrazu (media ID) lub None w razie niepowodzenia.
    """
    endpoint = f"{wordpress_url}/wp-json/wp/v2/media"

    try:
        # Pobranie obrazu z wygenerowanego URL
        print(f"Pobieranie obrazu z URL: {image_url}")
        response = requests.get(image_url)
        response.raise_for_status()
        
        # Konwersja na PNG za pomocą Pillow
        print("Konwersja obrazu na PNG...")
        image_data = response.content
        image = Image.open(io.BytesIO(image_data)).convert('RGBA')
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='PNG')
        output_buffer.seek(0)

        # Przygotowanie nazwy pliku
        original_filename = image_url.split('/')[-1]
        # Usuwanie parametrów GET i ograniczanie długości nazwy pliku
        filename_root = re.sub(r'\?.*$', '', original_filename.rsplit('.', 1)[0])
        filename_root = re.sub(r'[^a-zA-Z0-9_-]', '', filename_root)[:50]  # Usunięcie nieprawidłowych znaków i ograniczenie do 50 znaków
        filename_png = f"{filename_root}.png"
        
        # Przesyłanie obrazu do WordPress jako PNG
        print(f"Przesyłanie obrazu do WordPress jako {filename_png}...")
        files = {
            "file": (filename_png, output_buffer, 'image/png')
        }
        headers = {
            "Content-Disposition": f"attachment; filename={filename_png}",
        }

        upload_response = requests.post(
            endpoint,
            headers=headers,
            files=files,
            auth=HTTPBasicAuth(username, password)
        )

        # Obsługa odpowiedzi WordPress
        if upload_response.status_code == 201:
            media_id = upload_response.json()["id"]
            print(f"Obraz przesłany poprawnie z ID: {media_id}")
            return media_id
        else:
            print(f"Błąd podczas przesyłania obrazu: {upload_response.status_code}")
            print(upload_response.json())
            return None

    except requests.RequestException as req_err:
        print(f"Błąd HTTP podczas przesyłania obrazu: {req_err}")
    except Exception as e:
        print(f"Błąd podczas przesyłania obrazu: {e}")

    return None
def fetch_wordpress_categories(wordpress_url, username, password):
    """
    Pobiera listę kategorii z WordPressa.

    :param wordpress_url: URL Twojej strony WordPress (np. https://example.com).
    :param username: Nazwa użytkownika z uprawnieniami.
    :param password: Hasło użytkownika lub token aplikacji.
    :return: Lista kategorii (każda kategoria to słownik z informacjami).
    """
    endpoint = f"{wordpress_url}/wp-json/wp/v2/categories"

    try:
        response = requests.get(endpoint, auth=HTTPBasicAuth(username, password))
        response.raise_for_status()  # Sprawdzenie statusu odpowiedzi

        categories = response.json()
        cleaned_categories = [{"id": category["id"], "name": category["name"]} for category in categories]

        return cleaned_categories

    except requests.RequestException as e:
        print(f"Błąd podczas pobierania kategorii: {e}")
        return []