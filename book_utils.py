import re
import requests

def fetch_book_data(isbn):
    normalized_isbn = re.sub(r'\D', '', isbn)
    if not normalized_isbn:
        return {
            "ISBN": isbn,
            "Title": "Not Found",
            "Authors": "",
            "Publisher": "",
            "Published Date": "",
            "Categories": "",
            "Description": ""
        }

    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{normalized_isbn}"
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json().get("items")
        if items:
            volume_info = items[0]["volumeInfo"]
            return {
                "ISBN": isbn,
                "Title": volume_info.get("title", ""),
                "Authors": ", ".join(volume_info.get("authors", [])),
                "Publisher": volume_info.get("publisher", ""),
                "Published Date": volume_info.get("publishedDate", ""),
                "Categories": ", ".join(volume_info.get("categories", [])),
                "Description": volume_info.get("description", "")
            }
    return {"ISBN": isbn, "Title": "Not Found"}
