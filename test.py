import streamlit as st
import openpyxl
import json
import os
import google.generativeai as genai
import together
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OpenAI


# Load API dynamically based on user selection
def load_api(api_name, api_key):
    """Configures the selected AI API with an API key."""
    if api_name == "Gemini":
        genai.configure(api_key=api_key)
    elif api_name == "TogetherAI":
        together.api_key = api_key
    elif api_name == "AgenticAI":
        return OpenAI(api_key=api_key)
    return None


def parse_xlsx(file):
    """Extracts table structure from an XLSX file."""
    workbook = openpyxl.load_workbook(file)
    sheet = workbook.active
    columns = [cell.value for cell in sheet[1] if cell.value]
    return columns


def generate_sql(api_name, query, columns, agent=None):
    """Uses the selected AI API to generate an SQL query."""
    prompt = f"Generate an optimized and accurate SQL query for: '{query}'. The available columns are {columns}. Ensure proper syntax and efficiency."

    if api_name == "Gemini":
        model = genai.GenerativeModel("gemini-1.5-flash")  # Updated to Gemini 1.5 Flash
        response = model.generate_content(prompt)
    elif api_name == "TogetherAI":
        response = together.Completion.create(model="together-ai/gpt-neoxt", prompt=prompt, max_tokens=200)
    elif api_name == "AgenticAI" and agent:
        response = agent.run(prompt)

    return response.text if response else "Error generating SQL."


def main():
    """Streamlit UI for the Text-to-SQL generator."""
    st.set_page_config(page_title="Text-to-SQL Generator", layout="wide")
    st.title("🔍 AI-Powered Text-to-SQL Generator")
    st.write("Convert natural language queries into optimized SQL queries using your preferred AI API.")

    # User selects the API
    api_name = st.selectbox("Select AI API", ["Gemini", "TogetherAI", "AgenticAI"])
    api_key = st.text_input("Enter API Key", type="password")

    agent = None
    if api_key:
        agent = load_api(api_name, api_key)

    uploaded_file = st.file_uploader("📂 Upload an XLSX file", type=["xlsx"],
                                     help="Ensure the first row contains column names.")

    if uploaded_file:
        columns = parse_xlsx(uploaded_file)
        st.success("✅ File processed successfully!")
        st.write("### Available Columns:", columns)

        user_query = st.text_area("📝 Enter your natural language query:", height=100)

        if st.button("🚀 Generate SQL"):
            if user_query and api_key:
                with st.spinner("Generating SQL..."):
                    sql_query = generate_sql(api_name, user_query, columns, agent)
                    st.code(sql_query, language='sql')

                    # Store query history
                    if "query_history" not in st.session_state:
                        st.session_state.query_history = []
                    st.session_state.query_history.append(sql_query)
            else:
                st.warning("⚠️ Please enter a query and API key.")

        # Display Query History
        if "query_history" in st.session_state and st.session_state.query_history:
            st.write("### 📜 Query History")
            for idx, q in enumerate(st.session_state.query_history[::-1], start=1):
                with st.expander(f"Query {idx}"):
                    st.code(q, language='sql')

        # Export SQL Queries
        if st.button("📥 Export SQL Queries"):
            sql_export = "\n".join(st.session_state.query_history)
            st.download_button("Download SQL File", sql_export, "generated_queries.sql", "text/sql")


if __name__ == "__main__":
    main()
