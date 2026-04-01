import streamlit as st
import requests
import pandas as pd

# --- 1. CONFIGURATION & BRANDING ---
EMAIL = "your-email@example.com" 
USER_AGENT = f"ScholarlySearchTool/1.0 (mailto:{EMAIL})"
RIDER_CRANBERRY = "#820024" 
RIDER_PURPLE = "#572c9f"     

st.set_page_config(page_title="Rider University Library Search", layout="wide")

# CSS with DOUBLE BRACES {{ }} to prevent f-string SyntaxErrors
brand_css = f"""
<style>
    .stApp {{
        background-color: white !app;
        color: black;
    }}
    
    /* Fix the Search Input Box */
    div[data-baseweb="input"] {{
        background-color: white !important;
        border: 1px solid #ccc !important;
    }}
    
    input {{
        color: black !important;
    }}

    section[data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 2px solid {RIDER_CRANBERRY};
    }}

    h1, h2, h3, .stExpander p {{
        color: {RIDER_PURPLE} !important;
    }}

    div.stButton > button:first-child {{
        background-color: {RIDER_CRANBERRY};
        color: white;
        border-radius: 5px;
        border: none;
    }}
    
    div.stButton > button:first-child:hover {{
        background-color: {RIDER_PURPLE};
    }}

    header, footer {{visibility: hidden;}}
</style>
"""
st.markdown(brand_css, unsafe_allow_html=True)

# --- 2. API FUNCTIONS ---

def search_openalex(query):
    url = f"https://api.openalex.org/works?search={query}&mailto={EMAIL}&per-page=50"
    try:
        res = requests.get(url, timeout=15).json()
        return [{"Title": w.get('title'), "Year": w.get('publication_year'), "Source": "OpenAlex", "Link": w.get('doi') or w.get('id')} for w in res.get('results', [])]
    except: return []

def search_crossref(query):
    headers = {"User-Agent": USER_AGENT}
    url = f"https://api.crossref.org/works?query={query}&rows=50"
    try:
        res = requests.get(url, headers=headers, timeout=15).json()
        items = res.get('message', {}).get('items', [])
        return [{"Title": i.get('title', ['No Title'])[0], "Year": i.get('issued', {}).get('date-parts', [[None]])[0][0], "Source": "CrossRef", "Link": i.get('URL')} for i in items]
    except: return []

def search_pubmed(query):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    try:
        s_res = requests.get(f"{base_url}esearch.fcgi?db=pubmed&term={query}&retmax=50&retmode=json", timeout=15).json()
        ids = ",".join(s_res.get('esearchresult', {}).get('idlist', []))
        if not ids: return []
        sum_res = requests.get(f"{base_url}esummary.fcgi?db=pubmed&id={ids}&retmode=json", timeout=15).json()
        return [{"Title": sum_res['result'][uid].get('title'), "Year": sum_res['result'][uid].get('pubdate', '')[:4], "Source": "PubMed", "Link": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/"} for uid in s_res['esearchresult']['idlist'] if 'title' in sum_res['result'][uid]]
    except: return []

def search_loc(query):
    url = f"https://www.loc.gov/search/?q={query}&fo=json&count=50"
    try:
        res = requests.get(url, timeout=15).json()
        return [{"Title": i.get('title'), "Year": i.get('date')[:4] if i.get('date') else "n.d.", "Source": "Lib of Congress", "Link": i.get('url')} for i in res.get('results', [])]
    except: return []

def search_eric(query):
    url = f"https://api.ies.ed.gov/eric/?search={query}&format=json&rows=50"
    try:
        res = requests.get(url, timeout=15).json()
        return [{"Title": h.get('title'), "Year": h.get('pubyear'), "Source": "ERIC", "Link": f"https://eric.ed.gov/?id={h.get('id')}"} for h in res.get('hits', [])]
    except: return []

# --- 3. THE INTERFACE ---

def main():
    # Logo and Title
    LOGO_URL = "https://www.rider.edu/sites/default/files/styles/max_325x325/public/2022-09/Rider_U_Logo_Cranberry_RGB.png"
    
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(LOGO_URL, width=150)
    with col2:
        st.title("University Library Multi-Catalog Search")
    
    st.divider()

    with st.sidebar:
        st.header("Search Settings")
        
        # Labeled sections
        st.markdown(f"<p style='color:{RIDER_PURPLE}; font-weight:bold; margin-bottom:-10px;'>Search Topics</p>", unsafe_allow_html=True)
        user_query = st.text_input("topic_input", label_visibility="collapsed", placeholder="Enter research topics...")
        
        st.markdown(f"<p style='color:{RIDER_PURPLE}; font-weight:bold; margin-top:20px; margin-bottom:-10px;'>Databases</p>", unsafe_allow_html=True)
        catalogs = st.multiselect(
            "db_select",
            ["OpenAlex", "CrossRef", "PubMed", "Library of Congress", "ERIC"],
            default=["OpenAlex", "CrossRef", "PubMed", "Library of Congress", "ERIC"],
            label_visibility="collapsed"
        )
        
        st.write("") # Spacer
        run_search = st.button("Run Meta-Search", type="primary")

    if run_search:
        if not user_query:
            st.error("Please enter a search term.")
        else:
            results_dict = {}
            with st.spinner("Searching catalogs..."):
                if "OpenAlex" in catalogs: results_dict["OpenAlex"] = search_openalex(user_query)
                if "CrossRef" in catalogs: results_dict["CrossRef"] = search_crossref(user_query)
                if "PubMed" in catalogs: results_dict["PubMed"] = search_pubmed(user_query)
                if "Library of Congress" in catalogs: results_dict["Library of Congress"] = search_loc(user_query)
                if "ERIC" in catalogs: results_dict["ERIC"] = search_eric(user_query)

            for source, data in results_dict.items():
                if data:
                    df = pd.DataFrame(data).drop_duplicates(subset='Title')
                    with st.expander(f"📖 {source} ({len(df)} results)", expanded=True):
                        st.dataframe(
                            df,
                            column_config={"Link": st.column_config.LinkColumn("View Record")},
                            use_container_width=True,
                            hide_index=True
                        )
                else:
                    st.info(f"No results found for {source}.")

if __name__ == "__main__":
    main()
