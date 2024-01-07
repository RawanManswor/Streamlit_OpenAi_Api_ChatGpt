from openai import OpenAI
import time
import streamlit as st


class SaudiPersonalLawAssistant:
    def __init__(self):
        # Initialize the database configuration
        self.db_config = st.secrets["mysql"]

    def run(self):
        # Set Streamlit page configuration
        st.set_page_config(
            page_title="Saudi Personal Law Assistant",
            page_icon=":scales:"
        )
        st.header(":scales: Saudi Personal Law Assistant")
        # Add custom CSS to hide the App menu
        hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            </style>
        """
        st.markdown(hide_menu_style, unsafe_allow_html=True)
        st.markdown("""
        <style>
            .reportview-container {
                margin-top: -2em;
            }
            #MainMenu {visibility: hidden;}
            .stDeployButton {display:none;}
            footer {visibility: hidden;}
            #stDecoration {display:none;}
        </style>
        """, unsafe_allow_html=True)

        # try:
        # Get OpenAI API credentials from secrets
        api_key = st.secrets['OPENAI_API_KEY']
        assistant_id = st.secrets['ASSISTANT_ID']

        # Initialize OpenAI client
        st.session_state.client = OpenAI(api_key=api_key)

        # Check if the chat has already started
        if "messages" not in st.session_state:
            st.session_state.messages = []

        if "start_chat" not in st.session_state:
            st.session_state.start_chat = False

        # Start the chat
        if st.session_state.client:
            st.session_state.start_chat = True

        if st.session_state.start_chat:
            # Display existing messages in the chat
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Accept user input
            if prompt := st.chat_input(f"How can I assist you today..."):
                # Add user message to chat history
                st.session_state.messages.append({"role": "user", "content": prompt})
                # Display user message in chat message container
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Create a thread
                st.session_state.thread = st.session_state.client.beta.threads.create()

                # Add a Message to the thread
                st.session_state.client.beta.threads.messages.create(
                    thread_id=st.session_state.thread.id,
                    role="user",
                    content=prompt,
                )

                # Create a run to associate the assistant with the thread
                run = st.session_state.client.beta.threads.runs.create(
                    thread_id=st.session_state.thread.id,
                    assistant_id=assistant_id,
                )

                # Wait for the run to complete
                def wait_for_complete(run, thread):
                    while run.status == "queued" or run.status == "in_progress":
                        run = st.session_state.client.beta.threads.runs.retrieve(
                            thread_id=thread.id,
                            run_id=run.id,
                        )
                        time.sleep(1)
                    return run

                run = wait_for_complete(run, st.session_state.thread)

                # Retrieve the messages in the thread
                replies = st.session_state.client.beta.threads.messages.list(
                    thread_id=st.session_state.thread.id
                )

                # Process the assistant replies and format citations
                def process_replies(replies):
                    citations = []

                    for r in replies:
                        if r.role == "assistant":
                            message_content = r.content[0].text
                            annotations = message_content.annotations

                            for index, annotation in enumerate(annotations):
                                message_content.value = message_content.value.replace(
                                    annotation.text, f" [{index}]"
                                )

                                if file_citation := getattr(
                                    annotation, "file_citation", None
                                ):
                                    cited_file = st.session_state.client.files.retrieve(
                                        file_citation.file_id
                                    )
                                    citations.append(
                                        f"[{index}] {file_citation.quote} from {cited_file.filename}"
                                    )
                                elif file_path := getattr(annotation, "file_path", None):
                                    cited_file = st.session_state.client.files.retrieve(
                                        file_path.file_id
                                    )
                                    citations.append(
                                        f"[{index}] Click <here> to download {cited_file.filename}"
                                    )

                    full_response = message_content.value + "\n" + "\n".join(citations)
                    return full_response

                # Process the replies and add them to the chat history
                processed_response = process_replies(replies)
                st.session_state.messages.append(
                    {"role": "assistant", "content": processed_response}
                )
                # Display assistant's response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(processed_response, unsafe_allow_html=True)
    # except Exception as e:
    #     st.error("An error occurred. Please try again later.")

if __name__ == "__main__":
# Create an instance of SaudiPersonalLawAssistant class
    assistant = SaudiPersonalLawAssistant()
    # Run the Streamlit app
    assistant.run()