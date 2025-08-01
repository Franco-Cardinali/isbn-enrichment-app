import requests
import time
import streamlit as st

GOOGLE_API_KEY = st.secrets["api"]["google_books_key"]
GOOGLE_API_URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:{}&key={}"
OPENLIBRARY_API_URL = "https://openlibrary.org/api/books?bibkeys=ISBN:{}&format=json&jscmd=data"


def fetch_google_books(isbn, retries=3, delay=1):
    for attempt in range(retries):
        try:
            response = requests.get(GOOGLE_API_URL.format(isbn, GOOGLE_API_KEY), timeout=5)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and data["items"]:
                    volume_info = data["items"][0]["volumeInfo"]
                    return {
                        "ISBN": isbn,
                        "Title": volume_info.get("title", ""),
                        "Authors": ", ".join(volume_info.get("authors", [])),
                        "Publisher": volume_info.get("publisher", ""),
                        "PublishedDate": volume_info.get("publishedDate", ""),
                        "Description": volume_info.get("description", ""),
                        "PageCount": volume_info.get("pageCount", ""),
                        "Categories": ", ".join(volume_info.get("categories", [])),
                        "Language": volume_info.get("language", ""),
                        "PreviewLink": volume_info.get("previewLink", ""),
                        "Identifiers": ", ".join(
                            f"{id['type']}: {id['identifier']}" for id in volume_info.get("industryIdentifiers", [])
                        ),
                        "Source": "Google Books"
                    }
                else:
                    return {"ISBN": isbn, "Title": "Not Found", "Error": "No items found", "Source": "Google Books"}
            else:
                return {"ISBN": isbn, "Title": "Not Found", "Error": f"HTTP {response.status_code}", "Source": "Google Books"}
        except requests.RequestException as e:
            time.sleep(delay)
            return {"ISBN": isbn, "Title": "Not Found", "Error": str(e), "Source": "Google Books"}


def fetch_openlibrary(isbn):
    try:
        response = requests.get(OPENLIBRARY_API_URL.format(isbn), timeout=5)
        if response.status_code == 200:
            data = response.json()
            book_key = f"ISBN: {isbn}"
            if book_key in data:
                book = data[book_key]
                return {
                    "ISBN": isbn,
                    "Title": book.get("title", ""),
                    "Authors": ", ".join(author["name"] for author in book.get("authors", [])),
                    "Publisher": book.get("publishers", [{}])[0].get("name", ""),
                    "PublishedDate": book.get("publish_date", ""),
                    "Description": book.get("excerpt", {}).get("value", ""),
                    "PageCount": book.get("number_of_pages", ""),
                    "Categories": ", ".join(
                        subject["name"] if isinstance(subject, dict) else str(subject)
                        for subject in book.get("subjects", [])
                    ),
                    "Language": book.get("languages", [{}])[0].get("key", "").split("/")[-1] if book.get("languages") else "",
                    "PreviewLink": book.get("url", ""),
                    "Identifiers": f"ISBN_13: {isbn}",
                    "Source": "OpenLibrary"
                }
    except requests.RequestException:
        pass
    return None


def fetch_book_data(isbn):
    clean_isbn = isbn.replace("-", "").strip()
    result = fetch_google_books(clean_isbn)

    # Only accept Google result if it's valid
    if result and result.get("Title") and result.get("Title") != "Not Found" and "Error" not in result:
        result["Source"] = "Google Books"
        return result

    fallback = fetch_openlibrary(clean_isbn)
    if fallback and fallback.get("Title") and fallback.get("Title") != "Not Found":
        fallback["Source"] = "OpenLibrary"
        return fallback

    return {"ISBN": isbn, "Title": "Not Found", "Source": "None"}
