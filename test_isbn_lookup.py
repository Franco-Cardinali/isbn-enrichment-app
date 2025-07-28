import unittest
from book_utils import fetch_book_data  # Ensure book_utils.py is in the same directory or importable

class TestFetchBookData(unittest.TestCase):
    def test_valid_isbn(self):
        isbn = "9780143127741"
        result = fetch_book_data(isbn)
        print(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["ISBN"], isbn)
        self.assertNotEqual(result["Title"], "Not Found")

    def test_invalid_isbn(self):
        isbn = "0000000000000"
        result = fetch_book_data(isbn)
        print(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["Title"], "Not Found")

    def test_null_isbn(self):
        isbn = ""
        result = fetch_book_data(isbn)
        print(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["Title"], "Not Found")

def manual_isbn_lookup(isbn):
    result = fetch_book_data(isbn)
    print("\nBook Metadata:")
    for key, value in result.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    choice = input("Type 'T' to run tests or enter an ISBN to look it up: ").strip()
    if choice.lower() == "t":
        unittest.main()
    else:
        manual_isbn_lookup(choice)
