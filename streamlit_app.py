import asyncio
import sys
import os
import traceback
import threading

try:
    import streamlit as st
except ImportError:
    print(
        "Streamlit is not installed. Install all dependencies with\n"
        "`pip install -r requirements.txt` or run VCA.py for the CLI interface."
    )
    raise SystemExit(1)

# Warn if the script is executed directly instead of via ``streamlit run``.
if not st.runtime.scriptrunner.is_running_with_streamlit():
    print("This application should be launched with 'streamlit run streamlit_app.py'.")
    raise SystemExit(0)

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from VCA import _capture_analysis, _ensure_dependencies
except Exception as e:
    st.error(f"Failed to import application modules: {e}")
    st.info(
        "Check that all files are present and dependencies from requirements.txt are installed."
    )
    st.stop()


def _run_async(coro):
    """Execute an async coroutine even if a loop is already running."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, object] = {}
    error: dict[str, BaseException] = {}

    def _thread_runner() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except BaseException as e:
            error["err"] = e

    t = threading.Thread(target=_thread_runner)
    t.start()
    t.join()
    if "err" in error:
        raise error["err"]
    return result.get("value")


def main() -> None:
    """Streamlit application entry point."""
    missing = _ensure_dependencies()
    if missing:
        st.error(f"Missing required packages: {', '.join(missing)}")
        st.info("Please install missing packages using: pip install -r requirements.txt")
        st.stop()

    st.title("VC Portfolio Analyzer")

    url = st.text_input("Введите URL сайта фонда:", placeholder="https://example.com")

    if st.button("Запустить анализ") and url:
        if not url.startswith(("http://", "https://")):
            st.warning("Please enter a valid URL starting with http:// or https://")
        else:
            with st.spinner("Анализируем сайт..."):
                try:
                    results = _run_async(_capture_analysis(url))
                    st.text(results)
                except Exception as e:
                    st.error(f"Error during analysis: {e}")
                    st.exception(traceback.format_exc())
                    st.info("Please check the URL and try again.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # pragma: no cover - catch all for Streamlit
        st.error(f"Unhandled error: {e}")
        st.exception(traceback.format_exc())
