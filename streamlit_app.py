import streamlit as st
import requests
import os
from datetime import datetime

st.set_page_config(
    page_title="Code Sage",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

API_ENDPOINT = os.environ.get("API_ENDPOINT", "https://codesage-api.onrender.com")

if "history" not in st.session_state:
    st.session_state.history = []

st.title("🔍 CodeSage - Intelligent Code Review & Bug Prediction")
st.markdown("""
This tool uses AI to analyze your code, find bugs, and suggest improvements.
Just paste your code below, select the language, and let the AI do its work!
""")

with st.sidebar:
    st.header("About")
    st.markdown("""
    This tool uses Gemini 2.0 to analyze code and provide feedback.
    
    **Features:**
    - Identify potential bugs
    - Suggest code improvements
    - Follow best practices
    - Explain code issues
    """)
    
    st.header("Recent Reviews")
    if st.session_state.history:
        for idx, entry in enumerate(st.session_state.history):
            with st.expander(f"{entry['language']} - {entry['timestamp'][:10]}"):
                st.code(entry['code'][:100] + "..." if len(entry['code']) > 100 else entry['code'], 
                       language=entry['language'])
                if st.button("Load", key=f"load_{idx}"):
                    st.session_state.code = entry['code']
                    st.session_state.language = entry['language']
                    st.session_state.context = entry.get('context', '')
    else:
        st.info("No recent reviews")

col1, col2 = st.columns([2, 1])

with col1:
    if "code" not in st.session_state:
        st.session_state.code = ""
    
    code = st.text_area("Paste your code here:", 
                        value=st.session_state.code, 
                        height=400)
    
    col1a, col1b = st.columns(2)
    
    with col1a:
        language_options = [
            "Python", "Javascript", "Typescript", "Java", "C", "C++", "C#", 
            "Go", "Ruby", "PHP", "Rust", "Kotlin", "Swift", "HTML", "CSS"
        ]
        language = st.selectbox("Language", options=language_options, 
                                index=0 if "language" not in st.session_state else 
                                language_options.index(st.session_state.language) if st.session_state.language in language_options else 0)
    
    with col1b:
        context = st.text_input("Additional context (optional):", 
                                value="" if "context" not in st.session_state else st.session_state.context)
    
    if st.button("Review My Code", type="primary"):
        if not code.strip():
            st.error("Please enter some code to review")
        else:
            with st.spinner("Analyzing your code..."):
                try:
                    response = requests.post(
                        f"{API_ENDPOINT}/review",
                        json={
                            "code": code,
                            "language": language,
                            "context": context if context else None
                        },
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.session_state.last_review = result
                        
                        history_entry = {
                            "code": code,
                            "language": language,
                            "context": context,
                            "timestamp": datetime.now().isoformat(),
                            "request_id": result["request_id"]
                        }
                        st.session_state.history.insert(0, history_entry)
                        
                        if len(st.session_state.history) > 10:
                            st.session_state.history = st.session_state.history[:10]
                        
                        st.success("Review completed!")
                    else:
                        st.error(f"Error: {response.status_code} - {response.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

with col2:
    st.header("Review Results")
    
    if "last_review" in st.session_state:
        review = st.session_state.last_review
        
        if review["bugs_detected"]:
            with st.expander("🐛 Bugs Detected", expanded=True):
                for bug in review["bugs_detected"]:
                    severity_color = {
                        "low": "🟡",
                        "medium": "🟠",
                        "high": "🔴"
                    }.get(bug["severity"].lower(), "🟡")
                    
                    st.markdown(f"{severity_color} **Line {bug['line']}**: {bug['description']}")
                    
                    if bug.get("suggestion"):
                        st.code(bug["suggestion"],language=language)
        else:
            st.success("No bugs detected! 👍")
        
        if review["suggestions"]:
            with st.expander("💡 Suggestions", expanded=True):
                for suggestion in review["suggestions"]:
                    st.markdown(f"**Suggestion**: {suggestion['description']}")
                    
                    if suggestion.get("code_snippet"):
                        st.code(suggestion["code_snippet"])
        
        with st.expander("📝 Detailed Review"):
            st.markdown(review["review"])
        
        st.divider()
        st.subheader("Was this review helpful?")
        col_yes, col_no = st.columns(2)
        
        with col_yes:
            if st.button("👍 Yes"):
                try:
                    requests.post(
                        f"{API_ENDPOINT}/feedback",
                        json={
                            "request_id": review["request_id"],
                            "helpful": True
                        }
                    )
                    st.success("Thanks for your feedback!")
                except:
                    st.error("Failed to submit feedback")
        
        with col_no:
            if st.button("👎 No"):
                feedback = st.text_area("What could be improved?")
                if st.button("Submit Feedback"):
                    try:
                        requests.post(
                            f"{API_ENDPOINT}/feedback",
                            json={
                                "request_id": review["request_id"],
                                "helpful": False,
                                "comment": feedback
                            }
                        )
                        st.success("Thanks for your feedback!")
                    except:
                        st.error("Failed to submit feedback")
    else:
        st.info("Submit your code for review to see results here")