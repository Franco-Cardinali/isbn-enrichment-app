from concurrent.futures import ThreadPoolExecutor, as_completed
import streamlit as st
import pandas as pd
import time
from io import BytesIO
from datetime import datetime
from book_utils import fetch_book_data

# --- Session State Initialization ---
if "lookup_done" not in st.session_state:
    st.session_state.lookup_done = False
if "enriched_data" not in st.session_state:
    st.session_state.enriched_data = []
if "not_found_isbns" not in st.session_state:
    st.session_state.not_found_isbns = []
if "process_time" not in st.session_state:
    st.session_state.process_time = 0
if "failed_logs" not in st.session_state:
    st.session_state.failed_logs = []

# --- Streamlit UI ---
st.title("📚 ISBN Metadata Enrichment Tool")

# --- File Upload Section ---
uploaded_file = st.file_uploader("Upload Excel file with ISBNs", type=["xlsx"])
if uploaded_file:
    # Reset session state on new upload
    st.session_state.lookup_done = False
    st.session_state.enriched_data = []
    st.session_state.not_found_isbns = []
    st.session_state.process_time = 0
    st.session_state.failed_logs = []

# --- Concurrency Control ---
max_workers = 10  # Safer default to avoid overwhelming APIs

def parallel_lookup(isbn_list, max_workers=10):
    enriched_data = []
    not_found_isbns = []
    failed_logs = []

    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(isbn_list)
    completed = 0

    def safe_fetch(isbn):
        try:
            return fetch_book_data(isbn)
        except Exception as e:
            return {"ISBN": isbn, "Title": "Not Found", "Error": str(e)}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_isbn = {executor.submit(safe_fetch, isbn): isbn for isbn in isbn_list}
        for future in as_completed(future_to_isbn):
            isbn = future_to_isbn[future]
            try:
                book_data = future.result()
                enriched_data.append(book_data)
                if book_data.get("Title") == "Not Found":
                    not_found_isbns.append(isbn)
                    if "Error" in book_data:
                        failed_logs.append({"ISBN": isbn, "Error": book_data["Error"]})
            except Exception as e:
                enriched_data.append({"ISBN": isbn, "Title": "Not Found"})
                not_found_isbns.append(isbn)
                failed_logs.append({"ISBN": isbn, "Error": str(e)})
            completed += 1
            progress_bar.progress(completed / total)
            status_text.text(f"Processed {completed} of {total} ISBNs")

    return enriched_data, not_found_isbns, failed_logs
# --- Process Uploaded File ---
if uploaded_file and not st.session_state.lookup_done:
    df = pd.read_excel(uploaded_file, header=None, engine='openpyxl')  # No header
    isbn_list = df.iloc[:, 0].dropna().astype(str).str.strip().tolist()

    st.write(f"Found {len(isbn_list)} ISBNs. Starting lookups...")

    start_time = time.time()
    enriched_data, not_found_isbns, failed_logs = parallel_lookup(isbn_list, max_workers=max_workers)
    end_time = time.time()

    st.session_state.enriched_data = enriched_data
    st.session_state.not_found_isbns = not_found_isbns
    st.session_state.failed_logs = failed_logs
    st.session_state.process_time = end_time - start_time
    st.session_state.lookup_done = True

# --- Display Results and Download Buttons ---
if st.session_state.lookup_done:
    enriched_df = pd.DataFrame(st.session_state.enriched_data)
    found_df = enriched_df[enriched_df["Title"] != "Not Found"]

    date_str = datetime.now().strftime("%Y-%m-%d")

    output_found = BytesIO()
    with pd.ExcelWriter(output_found, engine='xlsxwriter') as writer:
        found_df.to_excel(writer, index=False, sheet_name='Enriched Data')
    st.download_button(
        label="📥 Download Found Metadata Excel",
        data=output_found.getvalue(),
        file_name=f"books_metadata_found_{date_str}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    if st.session_state.not_found_isbns:
        output_not_found = BytesIO()
        pd.DataFrame(st.session_state.not_found_isbns).to_excel(output_not_found, index=False, header=False)
        st.download_button(
            label="📥 Download Not Found ISBNs Excel",
            data=output_not_found.getvalue(),
            file_name=f"books_metadata_not_found_{date_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    if st.session_state.failed_logs:
        output_failed = BytesIO()
        pd.DataFrame(st.session_state.failed_logs).to_excel(output_failed, index=False)
        st.download_button(
            label="📥 Download Error Log Excel",
            data=output_failed.getvalue(),
            file_name=f"books_metadata_errors_{date_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    st.success("✅ Process finished!")

    # Format processing time
    total_seconds = int(st.session_state.process_time)
    if total_seconds >= 60:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_time = f"{minutes} minute(s) and {seconds} second(s)"
    else:
        formatted_time = f"{total_seconds} second(s)"
    st.info(f"⏱️ Total processing time: {formatted_time}")

    # Display summary with color-coded boxes
    total_count = len(st.session_state.enriched_data)
    found_count = len(found_df)
    not_found_count = len(st.session_state.not_found_isbns)

    st.markdown(f"""
    <div style='padding:10px; background-color:#e6ffe6; border-radius:5px; margin-top:10px'>
        ✅ Found ISBNs: <strong>{found_count}</strong>
    </div>
    <div style='padding:10px; background-color:#ffe6e6; border-radius:5px; margin-top:10px'>
        ❌ Not Found ISBNs: <strong>{not_found_count}</strong>
    </div>
    <div style='padding:10px; background-color:#f0f0f0; border-radius:5px; margin-top:10px'>
        📊 Total ISBNs Processed: <strong>{total_count}</strong>
    </div>
    """, unsafe_allow_html=True)

# --- Single ISBN Lookup Section ---
st.header("🔍 Single ISBN Lookup")
single_isbn = st.text_input("Enter an ISBN to look up")

if single_isbn:
    result = fetch_book_data(single_isbn)
    st.subheader("Book Metadata")
    for key, value in result.items():
        st.write(f"**{key}**: {value}")
