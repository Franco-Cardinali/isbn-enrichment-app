import requests
import time
import streamlit as st

GOOGLE_API_KEY = st.secrets.get("google_books_key", "")
GOOGLE_API_URL = "https://www.googleapis.com/books/v1/volumes?q=isbn:{}&key={}"
OPENLIBRARY_API_URL = "https://openlibrary.org/api/books?bibkeys=ISBN:{}&format=json&jscmd=data"

# ✅ Proxy endpoint hosted on Render
PROXY_API_URL = "https://isbn-enrichment-app.onrender.com/books?isbn={}"

def fetch_google_books(isbn, retries=3, delay=1, log_list=None):
    def log(msg):
        print(msg)  # ✅ Force log to appear in Streamlit logs
        if log_list is not None:
            log_list.append(msg)

    endpoint_url = PROXY_API_URL.format(isbn)
    for attempt in range(retries):
        try:
            response = requests.get(endpoint_url, timeout=5)
            log(f"[Proxy API] ISBN: {isbn} 🔄 Attempt {attempt+1} | URL: {endpoint_url} | Status: {response.status_code}")

            if response.status_code == 200:
                return response.json()
            else:
                try:
                    error_body = response.json()
                except ValueError:
                    error_body = response.text
                log(f"[Proxy API] ISBN: {isbn} ❌ HTTP {response.status_code} | Response: {error_body}")
                return {
                    "ISBN": isbn,
                    "Title": "Not Found",
                    "Error": f"HTTP {response.status_code}",
                    "Source": "Proxy",
                    "Log": {
                        "Endpoint": endpoint_url,
                        "Error": error_body
                    }
                }
        except requests.RequestException as e:
            log(f"[Proxy API] ISBN: {isbn} ❌ Request error: {e}")
            time.sleep(delay)
            return {
                "ISBN": isbn,
                "Title": "Not Found",
                "Error": str(e),
                "Source": "Proxy",
                "Log": {
                    "Endpoint": endpoint_url,
                    "Error": str(e)
                }
            }

    return {
        "ISBN": isbn,
        "Title": "Not Found",
        "Error": "Proxy failed after retries",
        "Source": "Proxy",
        "Log": {
            "Endpoint": endpoint_url,
            "Error": "Request failed"
        }
    }

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

def fetch_book_data(isbn, log_list=None):
    clean_isbn = isbn.replace("-", "").strip()
    result = fetch_google_books(clean_isbn, log_list=log_list)

    if result and result.get("Title") and result.get("Title") != "Not Found" and "Error" not in result:
        result["Source"] = "Google Books"
        return result

    fallback = fetch_openlibrary(clean_isbn)
    if fallback and fallback.get("Title") and fallback.get("Title") != "Not Found":
        fallback["Source"] = "OpenLibrary"
        return fallback

    return {
        "ISBN": isbn,
        "Title": "Not Found",
        "Source": "None",
        "Error": result.get("Error", "Unknown error"),
        "Log": result.get("Log", {})
    }
