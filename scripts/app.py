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
from pandasai import Agent
from pandasai.responses.streamlit_response import StreamlitResponse
from pandasai.llm import OpenAI
from dotenv import load_dotenv
from langchain import HuggingFaceHub
from langchain.chat_models import ChatOpenAI
from templates import css, bot_template, user_template, prompt_template
from pandasai.prompts import GeneratePythonCodePrompt
from PIL import Image


class FriendlyPrompt(GeneratePythonCodePrompt):
    template = prompt_template


def handle_userinput(user_question, agent):
    if st.session_state.file_list == [pd.DataFrame()]:
        st.write("Please load a CSV file first.")
        return
    if "chart" or "graph" or "plot" or "histogram" in user_question.lower():
        response = agent.chat(user_question, output_type="string")
    elif "table" in user_question.lower():
        response = agent.chat(user_question, output_type="dataframe")
    else:
        response = agent.chat(user_question)
    st.session_state.chat_history.append(user_question)
    st.session_state.chat_history.append(response)

    for i, message in enumerate(st.session_state.chat_history):
        # if i % 2 == 0 and type(message) in ['String', 'int']:
        #     st.write(user_template.replace(
        #         "{{MSG}}", str(message)), unsafe_allow_html=True)
        # elif type(message) in ['String', 'int']:
        #     st.write(bot_template.replace(
        #         "{{MSG}}", str(message)), unsafe_allow_html=True)
        # else:
        if i % 2 == 0:
            who = "user"
        else:
            who = "assitant"
        with st.chat_message(who):
            if "img_" in str(message):
                image = Image.open(message)
                st.image(image, use_column_width=True)
            else:
                st.write(message)


def main():
    load_dotenv()
    st.set_page_config(page_title="PDF Generator", page_icon=":robot_face:")
    st.write(css, unsafe_allow_html=True)
    # llm = HuggingFaceHub(repo_id='HuggingFaceH4/zephyr-7b-beta')
    # llm = ChatOpenAI(temperature=0, model='gpt-4-1106-preview')
    llm = OpenAI(model="gpt-4-1106-preview")
    st.header("PDF Generator")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "file_list" not in st.session_state:
        st.session_state.file_list = [pd.DataFrame()]
    if "agent" not in st.session_state:
        st.session_state.agent = Agent(
            st.session_state.file_list,
            config={
                "llm": llm,
                "verbose": True,
                "response_parser": StreamlitResponse,
                "custom_prompts": {"generate_python_code": FriendlyPrompt()},
                "custom_whitelisted_dependencies": ["random", "os"],
            },
            memory_size=20,
        )
    if st.button("Clear History"):
        st.session_state.chat_history = []
        st.session_state.agent = Agent(
            st.session_state.file_list,
            config={
                "llm": llm,
                "verbose": True,
                "response_parser": StreamlitResponse,
                "custom_prompts": {"generate_python_code": FriendlyPrompt()},
                "custom_whitelisted_dependencies": ["random", "os"],
            },
            memory_size=20,
        )

    with st.sidebar:
        st.subheader("Data")
        files = st.file_uploader(
            "Upload a CSV file", type=["csv"], accept_multiple_files=True
        )
        if st.button("Load Data"):
            with st.spinner("Loading Data..."):
                for file in files:
                    st.session_state.file_list.append(pd.read_csv(file))
                st.session_state.agent = Agent(
                    st.session_state.file_list,
                    config={
                        "llm": llm,
                        "verbose": True,
                        "response_parser": StreamlitResponse,
                        "custom_prompts": {"generate_python_code": FriendlyPrompt()},
                        "custom_whitelisted_dependencies": ["random", "os"],
                    },
                    memory_size=20,
                )
            st.success("Data Loaded!")
        if st.button("Clear loaded data"):
            st.session_state.file_list = [pd.DataFrame()]

    user_question = st.chat_input("Ask a question about your csv:")
    if user_question or st.session_state.chat_history != []:
        try:
            with st.spinner("Thinking..."):
                handle_userinput(user_question, st.session_state.agent)
        except Exception as e:
            st.error(e)


if __name__ == "__main__":
    main()
