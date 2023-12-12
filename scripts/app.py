# Copyright: (c) 2023, Jared Gage <jsgage7@gmail.com>
# Copyright: (c) 2023, ModsysML Project
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import streamlit as st
import pandas as pd
from pandasai import clear_cache
from pandasai.llm import OpenAI
from dotenv import load_dotenv
from helper_functions import *


def main():
    # streamlit page config
    st.set_page_config(page_title="PDF Generator", page_icon=":robot_face:")
    st.header("PDF Generator")

    # load OpenAI key and LLM model
    load_dotenv()
    llm = OpenAI(model="gpt-4-1106-preview")

    # initialize session state variables upon launch
    clear_cache()
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "file_list" not in st.session_state:
        st.session_state.file_list = [pd.DataFrame()]
    if "agent" not in st.session_state:
        st.session_state.agent = generate_agent(llm, st.session_state)

    # button to clear chat history, including LLM memory
    if st.button("Clear History"):
        st.session_state.chat_history = []
        st.session_state.agent = generate_agent(llm, st.session_state)
        clear_cache()

    # display chat history
    print_chat(st.session_state.chat_history)

    # sidebar section 1 contains file upload and button to clear data if no longer wanted
    with st.sidebar:
        st.subheader("Data")
        if st.button("Clear Loaded Data"):
            st.session_state.file_list = [pd.DataFrame()]
        files = st.file_uploader(
            "Upload a CSV file", type=["csv"], accept_multiple_files=True
        )
        if st.button("Load Data"):
            with st.spinner("Loading Data..."):
                for file in files:
                    st.session_state.file_list.append(pd.read_csv(file))
                st.session_state.agent = generate_agent(llm, st.session_state)
            st.success("Data Loaded!")

        # sidebar section 2 allows user to select which parts of conversation to export to PDF, and exports
        st.subheader("PDF Output")
        gen = st.checkbox("Prepare PDF")
        if gen:
            with st.form("pdf_form"):
                display_hist = [
                    f"{message.split(' ;; ')[0]}\n{message.split(' ;; ')[1]}"
                    for message in st.session_state.chat_history
                ]
                selected_messages = st.multiselect(
                    "Select messages:", display_hist, default=display_hist
                )
                download = st.form_submit_button("Download PDF")

            if download:
                try:
                    with st.spinner("Generating PDF..."):
                        generate_pdf(st.session_state, selected_messages)
                except Exception as e:
                    st.error(e)

    # input box for user to enter chat messages
    user_question = st.chat_input("Ask a question about your data:")
    if user_question:
        try:
            with st.spinner("Thinking..."):
                handle_userinput(user_question, st.session_state)
                # Refresh the page to update the displayed chat history
                st.rerun()
        except Exception as e:
            st.error(e)


if __name__ == "__main__":
    main()
