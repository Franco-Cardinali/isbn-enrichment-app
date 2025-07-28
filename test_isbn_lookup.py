import requests
import re
import unittest

def fetch_title_from_isbn(isbn):
    normalized_isbn = re.sub(r'\D', '', isbn)
    url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{normalized_isbn}"
    response = requests.get(url)
    if response.status_code == 200:
        items = response.json().get("items")
        if items:
            volume_info = items[0]["volumeInfo"]
            return volume_info.get("title", "Title Not Found")
    return "Title Not Found"

class TestISBNLookup(unittest.TestCase):
    def test_fetch_title_with_dashes(self):
        isbn = "978-0143127741"
        title = fetch_title_from_isbn(isbn)
        print(f"Title for ISBN {isbn}: {title}")
        self.assertIsInstance(title, str)
        self.assertNotEqual(title, "Title Not Found")

    def test_fetch_title_without_dashes(self):
        isbn = "9780143127741"
        title = fetch_title_from_isbn(isbn)
        print(f"Title for ISBN {isbn}: {title}")
        self.assertIsInstance(title, str)
        self.assertNotEqual(title, "Title Not Found")

if __name__ == "__main__":
    unittest.main()
