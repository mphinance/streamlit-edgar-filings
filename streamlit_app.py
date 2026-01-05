import streamlit as st
import os
import shutil
from pathlib import Path
from sec_edgar_downloader import Downloader
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
BASE_DIR = "sec-edgar-filings"
OUTPUT_DIR = "momentum_7_txt_uploads"

# --- HELPER FUNCTIONS ---
def clear_output_directory():
    """Cleans up previous runs to ensure fresh data."""
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR)

def zip_output_directory():
    """Zips the output directory for easy download."""
    shutil.make_archive(OUTPUT_DIR, 'zip', OUTPUT_DIR)
    return f"{OUTPUT_DIR}.zip"

# --- MAIN APP UI ---
st.title("📄 SEC Filing Downloader & Converter")
st.markdown("Download 10-K and 10-Q filings, convert them to clean text, and prepare them for NotebookLM.")

# Sidebar for Inputs
st.sidebar.header("Configuration")

# SEC requires a valid email for User-Agent
user_email = st.sidebar.text_input("Your Email (Required by SEC)", value="your.email@domain.com")
user_tickers = st.sidebar.text_area("Tickers (comma separated)", value="IREN, CRWV, GLXY, CRCL, HIMS, ZETA, ACHR")
user_forms = st.sidebar.multiselect("Forms to Download", ["10-K", "10-Q", "8-K"], default=["10-K", "10-Q"])

# Process Inputs
ticker_list = [t.strip().upper() for t in user_tickers.split(",") if t.strip()]

# --- DOWNLOAD LOGIC ---
if st.button("🚀 Start Download & Conversion"):
    if not user_email or "domain.com" in user_email:
        st.error("Please enter a valid email address. The SEC requires this for the User-Agent.")
    elif not ticker_list:
        st.error("Please enter at least one ticker symbol.")
    else:
        # Reset directories
        clear_output_directory()
        
        # Initialize Downloader
        dl = Downloader("Momentum Phinance", user_email)
        
        # Create a status container for real-time updates
        status_text = st.empty()
        progress_bar = st.progress(0)
        total_steps = len(ticker_list) * len(user_forms)
        step_count = 0
        
        results_log = []

        try:
            with st.status("Downloading and Converting...", expanded=True) as status:
                for ticker in ticker_list:
                    for form in user_forms:
                        step_count += 1
                        progress = step_count / total_steps
                        progress_bar.progress(progress)
                        
                        st.write(f"Fetching **{form}** for **{ticker}**...")
                        
                        try:
                            # Download the filing
                            dl.get(form, ticker, limit=1, download_details=True)

                            # Define path where SEC downloader puts files
                            ticker_path = Path(BASE_DIR) / ticker / form
                            
                            file_found = False
                            if ticker_path.exists():
                                for filing_folder in ticker_path.iterdir():
                                    if filing_folder.is_dir():
                                        for html_file in filing_folder.glob("*.html"):
                                            # Read and Parse
                                            with open(html_file, 'r', encoding='utf-8') as f:
                                                soup = BeautifulSoup(f.read(), "html.parser")
                                                
                                            # Convert to Text
                                            raw_text = soup.get_text(separator='\n\n', strip=True)
                                            
                                            new_name = f"{ticker}_{form}.txt"
                                            dest_path = os.path.join(OUTPUT_DIR, new_name)
                                            
                                            with open(dest_path, 'w', encoding='utf-8') as out_f:
                                                out_f.write(raw_text)
                                            
                                            st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;✅ Converted: `{new_name}`")
                                            results_log.append(new_name)
                                            file_found = True
                            
                            if not file_found:
                                st.warning(f"&nbsp;&nbsp;&nbsp;&nbsp;⚠️ No data found for {ticker} {form}")

                        except Exception as e:
                            st.error(f"Error processing {ticker} {form}: {e}")

                status.update(label="Process Complete!", state="complete", expanded=False)

            # --- COMPLETION & DOWNLOAD ---
            st.success("All tasks finished!")
            
            # Zip the files for user download
            zip_path = zip_output_directory()
            
            with open(zip_path, "rb") as fp:
                btn = st.download_button(
                    label="📥 Download All Files (ZIP)",
                    data=fp,
                    file_name="momentum_7_filings.zip",
                    mime="application/zip"
                )
                
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
