from dotenv import load_dotenv 
import os
from src.utils import fetch_sitemap_links, fetch_google_sheet_with_service_account, format_date_for_wordpress, update_google_sheet_row
from src.openai_integration import generate_outline_with_openai, generate_section_content, generate_cover_image
from src.wordpress_api import publish_to_wordpress, upload_image_to_wordpress, fetch_wordpress_categories
from prompts import outline_prompt, section_prompt
import json

# Wczytanie zmiennych z .env
load_dotenv()

# Debugowanie zmiennych środowiskowych
sitemap_url = os.getenv("SITEMAP_URL")
sheet_id = os.getenv("GOOGLE_SHEET_ID")
worksheet_name = os.getenv("WORKSHEET_NAME", "Sheet1")
openai_api_key = os.getenv("OPENAN_API_KEY")
wordpress_link = os.getenv("WORDPRESS_LINK")
wordpress_username = os.getenv("WORDPRESS_USERNAME")
wordpress_password = os.getenv("WORDPRESS_PASSWORD")

print(f"SITEMAP_URL: {sitemap_url}")
print(f"GOOGLE_SHEET_ID: {sheet_id}")
print(f"WORKSHEET_NAME: {worksheet_name}")

if not sitemap_url:
    print("Błąd: Brak zdefiniowanego URL mapy strony w pliku .env")
    exit()

# Pobranie linków z mapy strony
print("Pobieranie linków z mapy strony...")
links = fetch_sitemap_links(sitemap_url)
print(f"Pobrane linki: {links}")

if not sheet_id:
    print("Błąd: Brak ID arkusza Google w pliku .env")
    exit()

# Pobranie danych z Google Sheets za pomocą konta serwisowego
print("Pobieranie danych z Google Sheets...")
data = fetch_google_sheet_with_service_account(sheet_id, worksheet_name)

if not data:
    print("Brak danych do przetworzenia.")
    exit()

# Dodajemy indeks wiersza do każdego rekordu
for i, row in enumerate(data, start=2):  # Startujemy od 2, bo pierwszy wiersz to nagłówki
    row["rowIndex"] = i

# Filtruj tylko artykuły ze statusem pustym
filtered_data = [row for row in data if not row.get("Status")]

if not filtered_data:
    print("Brak artykułów do przetworzenia.")
    exit()

categories = fetch_wordpress_categories(wordpress_link, wordpress_username, wordpress_password)
print(categories)
for row in filtered_data:
    keyword = row.get("Main Keyword")
    date = row.get("Date")
    row_index = row.get("rowIndex")  # Pobranie indeksu wiersza

    if not keyword or not  date:
        print(f"Pominięto wiersz: {row}")
        continue

    print(f"Generowanie treści dla słowa kluczowego: {keyword}...")
    outline = generate_outline_with_openai(outline_prompt(keyword, links,categories), openai_api_key)
    print(f"\nOutline wygenerowany dla '{keyword}':\n{outline}\n")

    try:
        outline_data = json.loads(outline)  # Parsowanie wygenerowanego JSON
    except json.JSONDecodeError as e:
        print(f"Błąd parsowania JSON dla '{keyword}': {e}")
        continue

    sections_content = []
    for section in outline_data.get("sections", []):
        section_title = section.get("title", "Sekcja bez tytułu")
        prompt = section_prompt(section)
        print(f"Generowanie treści dla sekcji: {section_title}...")
        content = generate_section_content(prompt, openai_api_key)
        sections_content.append(content)

    final_content = "\n".join(sections_content).replace("\n\n", "\n").strip()

    print(f"Generowanie okładki dla '{keyword}'...")
    cover_image_url = generate_cover_image(keyword, openai_api_key)

    if cover_image_url:
        cover_image_id = upload_image_to_wordpress(
            cover_image_url, wordpress_link, wordpress_username, wordpress_password
        )
        print(f"Obraz okładki przesłany z ID: {cover_image_id}")
    else:
        print(f"Nie udało się wygenerować obrazu dla '{keyword}'.")
        cover_image_id = None

    article_json = {
        "title": outline_data.get("title", "Artykuł bez tytułu"),
        "slug": outline_data.get("slug", "brak-sluga"),
        "tags": outline_data.get("tags", []),
        "categories": outline_data.get("categories", []),
        "date": format_date_for_wordpress(date),
        "content": final_content,
        "featured_media": cover_image_id,  # Ustawienie ID grafiki jako okładki
    }

    result = publish_to_wordpress(article_json, wordpress_link, wordpress_username, wordpress_password)

    if result:
        print(f"Artykuł '{article_json['title']}' opublikowany pomyślnie.")
        update_google_sheet_row(sheet_id, worksheet_name, row_index, {"Status": "done"})
    else:
        print(f"Nie udało się opublikować artykułu '{article_json['title']}'.")
