import asyncio
import sys
import os

try:
    import streamlit as st
except ImportError:
    print(
        "Streamlit is not installed. Install all dependencies with\n"
        "`pip install -r requirements.txt` or run VCA.py for the CLI interface."
    )
    raise SystemExit(1)

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from VCA import _capture_analysis, _ensure_dependencies
    
    # Check for missing dependencies
    missing = _ensure_dependencies()
    if missing:
        st.error(f"Missing required packages: {', '.join(missing)}")
        st.info("Please install missing packages using: pip install -r requirements.txt")
        st.stop()
        
except ImportError as e:
    st.error(f"Import error: {str(e)}")
    st.info("Make sure all required packages are installed from requirements.txt")
    st.stop()
except Exception as e:
    st.error(f"Unexpected error: {str(e)}")
    st.stop()

st.title("VC Portfolio Analyzer")

url = st.text_input("Введите URL сайта фонда:", placeholder="https://example.com")

if st.button("Запустить анализ") and url:
    if not url.startswith(('http://', 'https://')):
        st.warning("Please enter a valid URL starting with http:// or https://")
    else:
        with st.spinner("Анализируем сайт..."):
            try:
                results = asyncio.run(_capture_analysis(url))
                st.text(results)
            except Exception as e:
                st.error(f"Error during analysis: {str(e)}")
                st.info("Please check the URL and try again.")
