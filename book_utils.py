import requests
import time

GOOGLE_API_URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:"
OPENLIBRARY_API_URL = "https://openlibrary.org/api/books?bibkeys=ISBN:{}&format=json&jscmd=data"

def fetch_google_books(isbn, retries=3, delay=1):
    for attempt in range(retries):
        try:
            response = requests.get(GOOGLE_API_URL + isbn, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and data["items"]:
                    volume_info = data["items"][0]["volumeInfo"]
                    return {
                        "ISBN": isbn,
                        "Title": volume_info.get("title", ""),
                        "Authors": ", ".join(volume_info.get("authors", [])),
                        "Publisher": volume_info.get("publisher", ""),
                        "PublishedDate": volume_info.get("publishedDate", "")
                    }
        except requests.RequestException:
            time.sleep(delay)
    return None

def fetch_openlibrary(isbn):
    try:
        response = requests.get(OPENLIBRARY_API_URL.format(isbn), timeout=5)
        if response.status_code == 200:
            data = response.json()
            book_key = f"ISBN:{isbn}"
            if book_key in data:
                book = data[book_key]
                return {
                    "ISBN": isbn,
                    "Title": book.get("title", ""),
                    "Authors": ", ".join(author["name"] for author in book.get("authors", [])),
                    "Publisher": book.get("publishers", [{}])[0].get("name", ""),
                    "PublishedDate": book.get("publish_date", "")
                }
    except requests.RequestException:
        pass
    return None

def fetch_book_data(isbn):
    result = fetch_google_books(isbn)
    if result and result.get("Title"):
        return result
    fallback = fetch_openlibrary(isbn)
    if fallback and fallback.get("Title"):
        return fallback
    return {"ISBN": isbn, "Title": "Not Found"}
