import openai
from PIL import Image
from dotenv import load_dotenv
import os
load_dotenv()
gpt_model= os.getenv("GPT_MODEL")
def generate_outline_with_openai(prompt, api_key, model=gpt_model):
    try:
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od tworzenia szczegółowych spisów treści w formacie json i SEO."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        print(f"Błąd podczas generowania spisu treści z OpenAI: {e}")
        return ""

def generate_section_content(prompt, api_key, model=gpt_model, max_tokens=3000):
    try:
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od pisania treści SEO i filozoficznych artykułów."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        print(f"Błąd podczas generowania treści: {e}")
        return "Nie udało się wygenerować treści."

def generate_cover_image(prompt, api_key, model=gpt_model):
    openai.api_key = api_key
    try:
        # Generowanie opisu obrazu
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Jesteś ekspertem od tworzenia opisów obrazów."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        image_description = response["choices"][0]["message"]["content"].strip()
        print(f"Opis wygenerowany dla obrazu: {image_description}")

        # Generowanie obrazu za pomocą OpenAI (DALL·E)
        image_response = openai.Image.create(
            prompt=image_description,
            n=1,
            size="1024x1024"
        )
        image_url = image_response["data"][0]["url"]
        print(f"Wygenerowany URL obrazu: {image_url}")
        return image_url

    except Exception as e:
        print(f"Błąd podczas generowania obrazu: {e}")
        return None


def generate_summary_and_faq(prompt, api_key, model=gpt_model):
    """
    Generuje w jednym promptcie:
    - Podsumowanie (HTML z <h2>Podsumowanie</h2><p>...</p>)
    - FAQ (HTML z <h2>FAQ</h2>, pytaniami w <h3>, odpowiedziami w <p>)
    """
    import openai
    openai.api_key = api_key

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "Jesteś pomocnym asystentem, który generuje podsumowanie i FAQ w HTML."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2000,
            temperature=0.7
        )
        # Zwracamy czysty HTML
        return response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        print(f"Błąd podczas generowania podsumowania i FAQ: {e}")
        return ""
