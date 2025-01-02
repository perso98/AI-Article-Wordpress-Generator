def outline_prompt(keyword, links, categories):
    """
    Generuje prompt dla OpenAI do stworzenia szczegółowego spisu treści w formacie JSON.

    :param keyword: Słowo kluczowe, na podstawie którego ma być wygenerowany spis treści.
    :param links: Lista linków, które mogą być przypisane do sekcji.
    :param categories: Lista kategorii (zawierająca id i nazwę).
    :return: Prompt jako string.
    """
    return (
        f"Na podstawie słowa kluczowego {keyword}, wygeneruj szczegółowy spis treści dla artykułu. "
        f"Struktura powinna być sformatowana jako JSON, aby ułatwić późniejszy podział. "
        f"GŁÓWNY TYTUŁ ARTYKUŁU powinien zawierać główne słowo kluczowe i być zoptymalizowany pod SEO, DAJ RÓWNIEŻ DOBRY SLUG POD SEO, "
        f"oraz DODAJ W TAGS dobrane do tematu tagi SEO (6 tagów).\n\n"
        f"W categories ma być tylko jeden ID, który pasuje do tej listy kategorii {categories}.\n\n"
        f"Upewnij się, że w categories znajdują się tylko numeryczne identyfikatory kategorii, np. categories: [6], bez dodatkowych informacji takich jak nazwa czy obiekt JSON."
        f"Proszę, aby każda sekcja i podsekcja uwzględniała sugestię stosowania odpowiednich tagów HTML, takich jak:\n"
        f" - <blockquote> dla cytatów,\n"
        f" - <table> tam, gdzie możesz zaproponować tabelaryczne przedstawienie danych.\n\n"
        f"Napisz też wstęp czyli 'introduction:' z formatowanie html w znacznikach <p></p> używaj pogrubień również i kursyw html, ma to być krótki wstęp z hookiem a także z wyjaśnieniem czego dowiesz się 3-4 zdania."
        f"Oto przykład formatu odpowiedzi:\n\n"
        f"{{\n"
        f'"title": "GŁÓWNY TYTUŁ ARTYKUŁU",\n'
        f'"tags": [],\n'
        f'"categories": [],\n'
        f'"slug": "slug",\n'
        f'"introduction:"<p></p>"'
        f'"sections": [\n'
        f"    {{\n"
        f'      "title": "[Tytuł sekcji 1]",\n'
        f'      "subsections": ["Podtytuł 1", "Podtytuł 2"]\n'
        f"    }},\n"
        f"    {{\n"
        f'      "title": "[Tytuł sekcji 2]",\n'
        f'      "subsections": ["Podtytuł 1", "Podtytuł 2"]\n'
        f"    }},\n"
        f"    {{\n"
        f'      "title": "[Tytuł sekcji 3]",\n'
        f'      "subsections": ["Podtytuł 1", "Podtytuł 2"]\n'
        f"    }}\n"
        f"  ]\n"
        f"}}\n\n"
        f"UWAGA: W 3 różnych sekcjach dodaj 'link': pod 'subsections':, wybierz 3 różne linki z tej listy: {links}, nie powtarzaj ich."
        f"UWAGA: W 3 różnych sekcjach dodaj 'table:true,' pod 'subsections':"
        f"Upewnij się, że klucz 'link:' i 'table:' jest zawsze na poziomie obiektu sekcji, a nie elementem tablicy 'subsections'."
        f"Rozmieść linki w różnych sekcjach (nie umieszczaj ich w kolejnych po sobie sekcjach).\n\n"
        f"UWAGA: Cały spis treści ma mieć dokładnie 7 sekcji. Każda sekcja powinna mieć różną liczbę podsekcji (3, 4 lub 5).\n\n"
        f"TWOIM OUTPUTEM MA BYĆ ZWYKŁY TEKST, BEZ CODE BLOCKÓW. NIE FORMATUJ ODPOWIEDZI JAKO KOD!"
        f"TWOIM OUTPUTEM MA BYC TYLKO JSON W {{}}"
    )

def section_prompt(section, article_title):
    """
    Generuje prompt dla sekcji artykułu z uwzględnieniem internal linking, jeśli w sekcji jest link.

    :param section: Słownik z informacjami o sekcji (tytuł, podrozdziały i opcjonalny link).
    :return: Prompt jako string.
    """
    section_title = section.get("title", "Sekcja bez tytułu")
    subsections = section.get("subsections", [])
    subsections_text = "\n- ".join(map(str, subsections))
    link = section.get("link")
    table = section.get("table")
    prompt = (
        f"JESTEŚ PROFESJONALNYM SEO WRITTEREM ARTYKUŁÓW, STARAJ SIĘ TON MIEĆ NIE FORMALNY A ZWYKŁY LUDZKI I PRZYJAZNY A TAKŻE CZĘSTO EKSPONUJ KORZYŚCI DLA CZYTELNIKA JEŚLI TO PASUJE:\n"
        f"Tytuł artykułu to : {article_title}"
        f"Napisz szczegółowy tekst dla sekcji \"{section_title}\". Uwzględnij następujące podrozdziały:\n"
        f"- {subsections_text}\n\n"
        f"Twój output ma być w formacie HTML, ale ma zawierać TYLKO treść, która znajdowałaby się w znaczniku `<body>`. "
        f"Nie dodawaj znacznika `<!DOCTYPE>`, `<html>`, `<head>` ani `<body>`. Zacznij od głównego nagłówka sekcji i używaj odpowiednich znaczników HTML dla treści. \n"
        f"** STOSUJ CZĘSTO DLA WAŻNYCH SŁÓW ITD POGRUBIENIA <b></b>, KURSYWY <em></em> INNE TAGI HTML ABY TEKST BYŁ BARDZO DYNAMICZNY\n"
        f"** UWAGA ZACZYNASZ OD ZNACZNIKA H2\n"
        f"** TREŚĆ MA BYĆ BARDZO ROZBUDOWANA I DŁUGA\n"
        f"***NIE UŻYWAJ CODEBLOCKÓW\n\n"
        f"***Twój output powinien brzmieć mądrze i refleksyjnie, jakby pisał go filozof, ale jednocześnie ma być prosty i zrozumiały dla każdego. "
        f"Użyj motywacyjnego stylu, dodaj płynność treści i spójność tonu. Wpleć przykłady z natury oraz analogie, aby uczynić przekaz bardziej obrazowym i inspirującym.***\n\n"
        f"***NIE UŻYWAJ ZBYT DUŻO METAFOR I NIE UŻYWAJ AKADEMICKIEGO STYLU***"
    )

    # Dodanie instrukcji dla internal linking, jeśli link jest obecny
    if link:
        prompt += (
            f"\n\nDODATKOWE INSTRUKCJE: W tej sekcji uwzględnij **internal linking**. "
            f"Skorzystaj z tego linku: {link}, aby stworzyć odpowiedni odnośnik. "
            f"Umieść ten link w miejscu słowa artykułu, który pasuje aby był odsyłaczem. "
            f"Na przykład użyj w zdaniu jako odnośnik do podobnego tematu."
        )
    if table:
        prompt += (
            f"\n\nDODATKOWE INSTRUKCJE: W tej sekcji uwzględnij **tabele*. "
            f"\n\n Stwórz z tagiem table jakąś tabele pasującą do treści sekcji"
        )
    return prompt


def image_prompt(keyword):
    return (
        f"Stwórz szczegółowy opis graficzny dla artykułu na temat '{keyword}'. "
        f"Okładka powinna być estetyczna, nowoczesna i inspirowana tematem: {keyword}. "
        f"Unikaj tekstu na grafice."
        f"To powinien być krótki opis na 2 zdania."
        f"Twoim outputem ma być tylko opis obrazka, nic nie dodawaj od siebie."
        f"Zacznij od: Stwórz grafikę realistyczną hd..."
    )
    
    
def summary_and_faq_prompt(content_text):
    return f"""
Przeanalizuj poniższy artykuł i wygeneruj 2 sekcje w formacie HTML (bez JSON, bez codeblocków):
1) Podsumowanie (2-3 zdania) w znacznikach <h3>Podsumowanie</h3><p> ... </p> Te podsumowanie to ma być takie zakończenie treści z przesłaniem masz nie streszczać ani nic z tych rzeczy
2) FAQ z 7 pytaniami i odpowiedziami (każda para Q/A w <h3> i <p>), poprzedź je <h2>FAQ</h2>

Artykuł:
\"\"\"
{content_text}
\"\"\"

TWOIM OUTPUTEM MA BYĆ TYLKO HTML - BEZ DODATKOWYCH KLUCZY, BEZ CODEBLOCKÓW, BEZ MARKDOWN.
    """.strip()