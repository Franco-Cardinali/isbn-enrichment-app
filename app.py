import streamlit as st
import pandas as pd
import requests
import time
import re
from io import BytesIO

# --- Google Books API Query ---
def fetch_book_data(isbn):
    normalized_isbn = re.sub(r'\D', '', isbn)  # Remove non-digit characters
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

# --- Streamlit UI ---
st.title("📚 ISBN Metadata Enrichment Tool")

uploaded_file = st.file_uploader("Upload Excel file with ISBNs", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, header=None)  # No header
    isbn_list = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()

    st.write(f"Found {len(isbn_list)} ISBNs. Starting enrichment...")

    enriched_data = []
    progress = st.progress(0)

    for i, isbn in enumerate(isbn_list):
        enriched_data.append(fetch_book_data(isbn))
        time.sleep(0.6)  # Rate limiting: ~100 requests/min
        progress.progress((i + 1) / len(isbn_list))

    enriched_df = pd.DataFrame(enriched_data)

    # --- Download Button ---
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        enriched_df.to_excel(writer, index=False, sheet_name='Enriched Data')
    st.download_button(
        label="📥 Download Enriched Excel",
        data=output.getvalue(),
        file_name="enriched_isbn_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
