import streamlit as st
import requests
import pandas as pd

# --- 1. CONFIGURATION & STYLING ---
# Change this to your actual email to use the "Polite Pool"
EMAIL = "your-email@example.com" 
USER_AGENT = f"ScholarlySearchTool/1.0 (mailto:{EMAIL})"

st.set_page_config(page_title="Library Research Portal", layout="wide")

# This CSS hides the Streamlit header/footer for a cleaner "embedded" look in LibGuides
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    [data-testid="stHeader"] {visibility: hidden;}
    </style>
    """
st.markdown(hide_style, unsafe_allow_html=True)

# --- 2. API SEARCH FUNCTIONS ---

def search_openalex(query):
    url = f"https://api.openalex.org/works?search={query}&mailto={EMAIL}"
    try:
        res = requests.get(url, timeout=10).json()
        return [{
            "Title": w.get('title'),
            "Year": w.get('publication_year'),
            "Source": "OpenAlex",
            "Link": w.get('doi') or w.get('id')
        } for w in res.get('results', [])]
    except: return []

def search_crossref(query):
    headers = {"User-Agent": USER_AGENT}
    url = f"https://api.crossref.org/works?query={query}&rows=10"
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        items = res.get('message', {}).get('items', [])
        return [{
            "Title": i.get('title', ['No Title'])[0],
            "Year": i.get('issued', {}).get('date-parts', [[None]])[0][0],
            "Source": "CrossRef",
            "Link": i.get('URL')
        } for i in items]
    except: return []

def search_pubmed(query):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    try:
        s_res = requests.get(f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmode=json", timeout=10).json()
        ids = ",".join(s_res.get('esearchresult', {}).get('idlist', []))
        if not ids: return []
        sum_res = requests.get(f"{base_url}esummary.fcgi?db=pubmed&id={ids}&retmode=json", timeout=10).json()
        results = []
        for uid in s_res['esearchresult']['idlist']:
            item = sum_res.get('result', {}).get(uid, {})
            results.append({
                "Title": item.get('title'),
                "Year": item.get('pubdate', '')[:4],
                "Source": "PubMed",
                "Link": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"
            })
        return results
    except: return []

def search_loc(query):
    url = f"https://www.loc.gov/search/?q={query}&fo=json"
    try:
        res = requests.get(url, timeout=10).json()
        return [{
            "Title": i.get('title'),
            "Year": i.get('date')[0:4] if i.get('date') else "n.d.",
            "Source": "Lib of Congress",
            "Link": i.get('url')
        } for i in res.get('results', [])]
    except: return []

# --- 3. THE WEB INTERFACE ---

def main():
    st.title("📚 Multi-Catalog Research Search")
    
    with st.sidebar:
        st.header("Search Parameters")
        user_query = st.text_input("Keywords:", placeholder="Enter search terms...")
        
        catalogs = st.multiselect(
            "Select Databases:",
            ["OpenAlex", "CrossRef", "PubMed", "Library of Congress"],
            default=["OpenAlex", "CrossRef", "PubMed", "Library of Congress"]
        )
        
        run_search = st.button("Search All Catalogs", type="primary")

    if run_search:
        if not user_query:
            st.error("Please enter a search term first.")
        else:
            all_results = []
            with st.spinner("Searching databases..."):
                if "OpenAlex" in catalogs:
                    all_results.extend(search_openalex(user_query))
                if "CrossRef" in catalogs:
                    all_results.extend(search_crossref(user_query))
                if "PubMed" in catalogs:
                    all_results.extend(search_pubmed(user_query))
                if "Library of Congress" in catalogs:
                    all_results.extend(search_loc(user_query))

            if all_results:
                df = pd.DataFrame(all_results).drop_duplicates(subset='Title')
                st.success(f"Found {len(df)} unique results.")
                
                st.dataframe(
                    df,
                    column_config={"Link": st.column_config.LinkColumn("View Record")},
                    use_container_width=True,
                    hide_index=True
                )
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", data=csv, file_name="results.csv", mime="text/csv")
            else:
                st.warning("No results found. Try different keywords.")

if __name__ == "__main__":
    main()
