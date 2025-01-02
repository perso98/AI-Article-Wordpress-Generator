from dotenv import load_dotenv
import os
from src.utils import fetch_sitemap_links, fetch_google_sheet_with_service_account, format_date_for_wordpress, update_google_sheet_row
from src.openai_integration import generate_outline_with_openai, generate_section_content, generate_cover_image, generate_summary_and_faq
from src.wordpress_api import publish_to_wordpress, upload_image_to_wordpress, fetch_wordpress_categories
from prompts import outline_prompt, section_prompt, image_prompt, summary_and_faq_prompt
import json
from bs4 import BeautifulSoup
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

    if not keyword or not date:
        print(f"Pominięto wiersz: {row}")
        continue

    print(f"Generowanie treści dla słowa kluczowego: {keyword}...")
    outline = generate_outline_with_openai(outline_prompt(keyword, links, categories), openai_api_key)
    print(f"\nOutline wygenerowany dla '{keyword}':\n{outline}\n")

    try:
        outline_data = json.loads(outline)  # Parsowanie wygenerowanego JSON
    except json.JSONDecodeError as e:
        print(f"Błąd parsowania JSON dla '{keyword}': {e}")
        continue
    
    # Generowanie sekcji treści
    sections_content = []
    for section in outline_data.get("sections"):
        section_title = section.get("title", "Sekcja bez tytułu")
        prompt_for_section = section_prompt(section, outline_data.get("title"))
        print(f"Generowanie treści dla sekcji: {section_title}...")
        content = generate_section_content(prompt_for_section, openai_api_key)
        sections_content.append(content)

    introduction = outline_data.get("introduction", "")

    # Dodanie wstępu do początku treści artykułu
    final_content = introduction+ "\n".join(sections_content).replace("\n\n", "\n").strip()
    # 1) Parsujemy HTML -> tekst
    parsed_text = BeautifulSoup(final_content, "html.parser").get_text(" ", strip=True)

    # 2) Wywołujemy nową funkcję do wygenerowania HTML z podsumowaniem i FAQ
    print("Generowanie Podsumowania + FAQ...")
    prompt_for_summary_and_faq = summary_and_faq_prompt(parsed_text)
    summary_and_faq_html = generate_summary_and_faq(prompt_for_summary_and_faq, openai_api_key)

    # 3) Dodajemy to do final_content
    #    (jeśli summary_and_faq_html jest puste, nic się nie stanie)
    final_content += "\n" + summary_and_faq_html
    print(outline_data.get("title") + final_content)
    # Generowanie obrazu okładki
    cover_image_url = None
    for attempt in range(3):  # Maksymalnie 3 próby generacji obrazu
        print(f"Próba {attempt + 1}: Generowanie okładki dla '{keyword}'...")
        cover_image_prompt = image_prompt(keyword)
        cover_image_url = generate_cover_image(cover_image_prompt , openai_api_key)
        if cover_image_url:
            break
        print(f"Nie udało się wygenerować obrazu dla '{keyword}'. Próba {attempt + 1} nieudana.")

    # Przesyłanie obrazu do WordPress
    cover_image_id = None
    if cover_image_url:
        for attempt in range(3):  # Maksymalnie 3 próby przesyłania obrazu do WordPress
            print(f"Próba {attempt + 1}: Przesyłanie obrazu do WordPress...")
            cover_image_id = upload_image_to_wordpress(
                cover_image_url, wordpress_link, wordpress_username, wordpress_password
            )
            if cover_image_id:
                print(f"Obraz przesłany poprawnie z ID: {cover_image_id}")
                break
            print(f"Próba {attempt + 1}: Nie udało się przesłać obrazu do WordPress.")

    # Przygotowanie danych do publikacji
    article_json = {
        "title": outline_data.get("title"),
        "slug": outline_data.get("slug", "brak-sluga"),
        "tags": outline_data.get("tags", []),
        "categories": outline_data.get("categories", []),
        "date": format_date_for_wordpress(date),
        "content": final_content,
        "featured_media": cover_image_id,  # Ustawienie ID grafiki jako okładki
    }

    # Publikacja artykułu w WordPress
    result = None
    for attempt in range(3):  # Maksymalnie 3 próby publikacji artykułu
        print(f"Próba {attempt + 1}: Publikacja artykułu '{article_json['title']}'...")
        result = publish_to_wordpress(article_json, wordpress_link, wordpress_username, wordpress_password)
        if result:
            break
        print(f"Próba {attempt + 1}: Nie udało się opublikować artykułu.")

    if result:
        print(f"Artykuł '{article_json['title']}' opublikowany pomyślnie.")
        update_google_sheet_row(sheet_id, worksheet_name, row_index, {"Status": "done"})
    else:
        print(f"Nie udało się opublikować artykułu '{article_json['title']}'.")
