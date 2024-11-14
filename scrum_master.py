import streamlit as st
import google.generativeai as genai
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
# Define the Google Custom Search API method to search online for relevant results
def search_online(query):
    api_key = os.getenv("GOOGLE_API_KEY")
    cse_id = os.getenv("CSE_ID")
    if not api_key or not cse_id:
        st.error("API key or Custom Search Engine ID is missing.")
        return []

    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cse_id}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        search_results = response.json()

        # Extract titles and snippets of relevant search results
        online_references = []
        if 'items' in search_results:
            for result in search_results['items']:
                title = result.get('title', 'No title')
                snippet = result.get('snippet', 'No snippet available')
                link = result.get('link', '#')
                online_references.append(f"**{title}**\n{snippet}\n[Read more]({link})")
        else:
            st.warning("No relevant online references found.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching search results: {e}")
        return []
    
    return online_references

# Function to generate prompt with online references
def make_rag_prompt(query):
    online_references = search_online(query)
    online_references_str = "\n".join(online_references) if online_references else "No online references found."

    prompt = (
        f"You are an intelligent assistant that answers questions using only online references. "
        f"Please answer the question by using information from online resources. "
        f"Make sure your answer is accurate, well-rounded, and integrates the information effectively.\n\n"
        f"QUESTION: '{query}'\n"
        f"ONLINE REFERENCES:\n{online_references_str}\n\n"
        f"ANSWER:"
    )
    return prompt, online_references

# Function to generate response from AI model
def generate_response(user_prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')  # Ensure model name is correct
        answer = model.generate_content(user_prompt)
        return answer.text
    except Exception as e:
        st.error(f"Error generating response: {e}")
        return "Sorry, I couldn't generate a response at the moment."

# Function to create answer from prompt
def generate_answer(query):
    prompt, online_references = make_rag_prompt(query)
    answer = generate_response(prompt)
    return answer, online_references

# Initialize session state for managing multiple chat sessions
if "chat_sessions" not in st.session_state:
    st.session_state["chat_sessions"] = {}
if "current_session_id" not in st.session_state:
    # Create the first chat session
    st.session_state["current_session_id"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["chat_sessions"][st.session_state["current_session_id"]] = []

# Sidebar for managing chat sessions
col11, col22 = st.sidebar.columns([1, 3])  # 1:3 ratio
col11.image("logo.png", width=50)  # Replace "logo.png" with the path to your logo file
col22.subheader("Scrum Mentor")
# st.sidebar.markdown("---")

# Button to start a new chat session
if st.sidebar.button("🆕 New Chat"):
    new_session_id = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["current_session_id"] = new_session_id
    st.session_state["chat_sessions"][new_session_id] = []

# Option to end the session and clear chat history
if st.sidebar.button("🛑 End Session"):
    st.session_state["chat_sessions"].clear()
    st.session_state["current_session_id"] = None
    st.success("All sessions ended and memory cleared.")

st.sidebar.subheader("Chat Sessions")
for index, session_id in enumerate(st.session_state["chat_sessions"]):
    session_date = datetime.strptime(session_id, "%Y-%m-%d %H:%M:%S").strftime("%Y-%b-%d %H:%M")
    if st.sidebar.button(f"{session_date}", key=f"{session_id}_{index}"):
        st.session_state["current_session_id"] = session_id


# Main chat area
st.title("Agile Development AI Assistant 💁")
st.markdown("Welcome to Agile Mentor! Ask any question to get started.")

# Display the current session's chat history
current_session = st.session_state["chat_sessions"].get(st.session_state["current_session_id"], [])
for message in current_session:
    if message["role"] == "user":
        st.chat_message("user").markdown(f"{message['content']}")
    else:
        st.chat_message("assistant").markdown(f"{message['content']}")

# Input area for new user message
if "query_input" not in st.session_state:
    st.session_state.query_input = ""  # Initialize the input field state

# Define the submit function that will reset the input field after submission
def submit():
    query = st.session_state.query_input
    if query:
        # Append the user query to the current session
        current_session.append({"role": "user", "content": query})

        # Generate and display the assistant's response
        with st.spinner("Generating response..."):
            answer, online_references = generate_answer(query)
        current_session.append({"role": "assistant", "content": answer})

        # Display the new messages in the chat
        # st.chat_message("user").markdown(f"{query}")
        # st.chat_message("assistant").markdown(f"{answer}")

        # Show references for the latest answer
        # if online_references:
        #     st.write("---")
        #     st.subheader("References:")
        #     for reference in online_references[:3]:
        #         st.write(reference)

        # Clear the input field after processing
        st.session_state.query_input = ""  # Reset session state to clear the input

# Input box for the user to enter their message
st.text_input('💬 Enter your message:', key='query_input', on_change=submit)
