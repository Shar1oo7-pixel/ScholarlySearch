import streamlit as st
import requests
import pandas as pd

# --- 1. CONFIGURATION & BRANDING ---
EMAIL = "your-email@example.com" 
USER_AGENT = f"ScholarlySearchTool/1.0 (mailto:{EMAIL})"
RIDER_CRANBERRY = "#820024" 
RIDER_PURPLE = "#572c9f"     

st.set_page_config(page_title="Rider University Library Search", layout="wide")

# Updated CSS for white inputs and labeled sections
brand_css = f"""
<style>
    /* Force White Background for everything */
    .stApp {{
        background-color: white;
        color: black;
    }}
    
    /* Fix the Search Input Box (Search Topics) */
    div[data-baseweb="input"] {{
        background-color: white !important;
        border: 1px solid #ccc !important;
    }}
    
    input {{
        color: black !important;
        background-color: white !important;
    }

    /* Style the Sidebar */
    section[data-testid="stSidebar"] {{
        background-color: #ffffff;
        border-right: 2px solid {RIDER_CRANBERRY};
    }}

    /* Headers in Rider Purple */
    h1, h2, h3 {{
        color: {RIDER_PURPLE} !important;
    }}

    /* Cranberry Search Button */
    div.stButton > button:first-child {{
        background-color: {RIDER_CRANBERRY};
        color: white;
        border-radius: 5px;
        border: none;
    }}
    
    div.stButton > button:first-child:hover {{
        background-color: {RIDER_PURPLE};
    }}

    /* Hide Streamlit Header/Footer */
    header, footer {{visibility: hidden;}}
</style>
"""
st.markdown(brand_css, unsafe_allow_html=True)

# --- 2. API FUNCTIONS (Remaining the same) ---
# [Keep your search_openalex, search_crossref, search_pubmed, search_loc, search_eric functions here]

# --- 3. THE INTERFACE ---

def main():
    # LOGO SECTION
    # You can replace this URL with a Rider University Library logo URL
    LOGO_URL = "https://www.rider.edu/sites/default/files/styles/max_325x325/public/2022-09/Rider_U_Logo_Cranberry_RGB.png"
    
    col1, col2 = st.columns([1, 5])
    with col1:
        st.image(LOGO_URL, width=150)
    with col2:
        st.title("University Library Multi-Catalog Search")
    
    st.divider()

    with st.sidebar:
        st.header("Search Settings")
        
        # Labeling the input boxes clearly
        st.write("**Search Topics**")
        user_query = st.text_input("Enter keywords:", label_visibility="collapsed", placeholder="e.g., Higher Education Trends")
        
        st.write("**Databases**")
        catalogs = st.multiselect(
            "Select to search:",
            ["OpenAlex", "CrossRef", "PubMed", "Library of Congress", "ERIC"],
            default=["OpenAlex", "CrossRef", "PubMed", "Library of Congress", "ERIC"],
            label_visibility="collapsed"
        )
        
        run_search = st.button("Run Meta-Search", type="primary")

    if run_search:
        if not user_query:
            st.error("Please enter a search term.")
        else:
            results_dict = {}
            with st.spinner("Searching..."):
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

if __name__ == "__main__":
    main()
