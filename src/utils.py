import requests
import xml.etree.ElementTree as ET
import gspread

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

def update_google_sheet_row(sheet_id, worksheet_name, row_index, updates):
    """
    Aktualizuje określony wiersz w Google Sheets.

    :param sheet_id: ID arkusza Google.
    :param worksheet_name: Nazwa zakładki w arkuszu.
    :param row_index: Indeks wiersza do aktualizacji (1-indexed, czyli zaczyna się od 1).
    :param updates: Słownik, gdzie klucz to nazwa kolumny, a wartość to nowa wartość.
    :return: None
    """
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
    service = build('sheets', 'v4', credentials=creds)

    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=sheet_id, range=f"{worksheet_name}!A1:Z1").execute()
    headers = result.get('values', [[]])[0]

    column_updates = {}
    for col_name, value in updates.items():
        if col_name in headers:
            column_index = headers.index(col_name) + 1
            column_updates[column_index] = value

    requests_data = []
    for column_index, value in column_updates.items():
        # Zaktualizowanie odpowiedniej komórki
        cell_range = f"{worksheet_name}!{chr(64 + column_index)}{row_index}"
        requests_data.append({
            'range': cell_range,
            'values': [[value]]
        })

    body = {'valueInputOption': 'USER_ENTERED', 'data': requests_data}
    service.spreadsheets().values().batchUpdate(spreadsheetId=sheet_id, body=body).execute()
    print(f"Zaktualizowano wiersz {row_index} w arkuszu {worksheet_name}.")


def fetch_sitemap_links(sitemap_url):
    """
    Pobiera wszystkie linki z mapy strony XML.
    
    :param sitemap_url: URL mapy strony (np. https://twojblog.pl/sitemap.xml)
    :return: Lista linków (str)
    """
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()  # Sprawdzenie, czy żądanie się powiodło

        # Parsowanie XML
        root = ET.fromstring(response.content)
        links = [
            url.text for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc")
        ]

        return links

    except requests.RequestException as e:
        print(f"Błąd HTTP: {e}")
        return []
    except ET.ParseError as e:
        print(f"Błąd XML: {e}")
        return []


import gspread
import traceback

def fetch_google_sheet_with_service_account(sheet_id, worksheet_name="Sheet1"):
    """
    Pobiera dane z arkusza Google Sheets za pomocą konta serwisowego.
    
    :param sheet_id: ID arkusza Google (z URL).
    :param worksheet_name: Nazwa zakładki w arkuszu.
    :return: Lista wierszy jako listy słowników.
    """
    try:
        print("Ładowanie pliku JSON z kontem serwisowym...")
        gc = gspread.service_account(filename="./credentials.json")

        print(f"Łączenie z arkuszem o ID: {sheet_id}")
        sheet = gc.open_by_key(sheet_id)

        print(f"Otwieranie zakładki: {worksheet_name}")
        worksheet = sheet.worksheet(worksheet_name)

        print("Pobieranie danych...")
        records = worksheet.get_all_records()

        print("Dane zostały pobrane pomyślnie!")
        return records

    except gspread.SpreadsheetNotFound:
        print("Błąd: Arkusz nie został znaleziony. Sprawdź ID arkusza i dostęp konta serwisowego.")
    except gspread.WorksheetNotFound:
        print(f"Błąd: Zakładka '{worksheet_name}' nie została znaleziona w arkuszu.")
    except Exception as e:
        print("Błąd: Wystąpił nieoczekiwany problem podczas pobierania danych z Google Sheets.")
        print(traceback.format_exc())  # Wyświetlenie szczegółów błędu
    return []


import datetime

# Funkcja do konwersji daty na ISO 8601
def format_date_for_wordpress(date):
    try:
        # Oczekujemy formatu 'YYYY-MM-DD'
        parsed_date = datetime.datetime.strptime(date, "%Y-%m-%d")
        # Zwróć datę w formacie ISO 8601 z godziną 00:00:00
        return parsed_date.isoformat()
    except ValueError:
        print(f"Błąd: Nieprawidłowy format daty '{date}'")
        return None


import requests
from requests.auth import HTTPBasicAuth

def ensure_tags_exist(tags, wordpress_url, username, password):
    """
    Tworzy brakujące tagi i zwraca ich ID.
    
    :param tags: Lista nazw tagów.
    :param wordpress_url: URL do strony WordPress.
    :param username: Nazwa użytkownika WordPress.
    :param password: Hasło użytkownika WordPress.
    :return: Lista ID tagów.
    """
    endpoint = f"{wordpress_url}/wp-json/wp/v2/tags"
    tag_ids = []

    for tag in tags:
        # Sprawdź, czy tag istnieje
        response = requests.get(endpoint, params={"search": tag}, auth=HTTPBasicAuth(username, password))
        
        if response.status_code == 200 and response.json():
            # Jeśli tag istnieje, dodaj jego ID
            tag_ids.append(response.json()[0]['id'])
        else:
            # Jeśli tag nie istnieje, utwórz go
            create_response = requests.post(
                endpoint,
                json={"name": tag},
                auth=HTTPBasicAuth(username, password)
            )
            if create_response.status_code == 201:
                tag_ids.append(create_response.json()['id'])
            else:
                print(f"Błąd podczas tworzenia taga '{tag}': {create_response.json()}")

    return tag_ids
