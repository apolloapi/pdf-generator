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
from pandasai import Agent, SmartDataframe, clear_cache
from pandasai.responses.streamlit_response import StreamlitResponse
from pandasai.llm import OpenAI
from pandasai.prompts import GeneratePythonCodePrompt
from dotenv import load_dotenv
from langchain.llms import HuggingFaceHub
from templates import prompt_template
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle
import openai


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
    print_chat()


def print_chat():
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            who = "user"
        else:
            who = "assitant"
        with st.chat_message(who):
            if "img_" in str(message):
                image = PILImage.open(message)
                st.image(image, use_column_width=True)
            else:
                st.write(message)


def generate_agent(llm):
    return Agent(
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


def generate_pdf(agent):
    client = OpenAI()
    doc = SimpleDocTemplate("transparency_report.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        "CustomStyle",
        parent=styles["Normal"],
        spaceAfter=12,
    )
    content = []
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            prompt = f"Rephrase this question into a concise heading in title case: {message}. Ensure the heading is not a question."
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
            )
            content.append(
                Paragraph(completion.choices[0].message.content, styles["Heading1"])
            )
        else:
            if isinstance(message, SmartDataframe):
                df = message
                data = [
                    df.columns[
                        :,
                    ].tolist()
                ] + df.values.tolist()
                t = Table(data)
                t.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("INNERGRID", (0, 0), (-1, -1), 0.25, "black"),
                            ("BOX", (0, 0), (-1, -1), 0.25, "black"),
                        ]
                    )
                )
                content.append(t)

            elif "img_" in str(message):
                content.append(Image(message, width=400, height=400))

            else:
                content.append(Paragraph(message, custom_style))
    doc.build(content)


def main():
    load_dotenv()
    st.set_page_config(page_title="PDF Generator", page_icon=":robot_face:")
    # llm = HuggingFaceHub(repo_id='gpt2-medium')
    llm = OpenAI(model="gpt-4-1106-preview")
    st.header("PDF Generator")
    clear_cache()

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "file_list" not in st.session_state:
        st.session_state.file_list = [pd.DataFrame()]
    if "agent" not in st.session_state:
        st.session_state.agent = generate_agent(llm)
    if st.button("Clear History"):
        st.session_state.chat_history = []
        st.session_state.agent = generate_agent(llm)

    with st.sidebar:
        st.subheader("Data")
        files = st.file_uploader(
            "Upload a CSV file", type=["csv"], accept_multiple_files=True
        )
        if st.button("Load Data"):
            with st.spinner("Loading Data..."):
                for file in files:
                    st.session_state.file_list.append(pd.read_csv(file))
                st.session_state.agent = generate_agent(llm)
            st.success("Data Loaded!")
        if st.button("Clear loaded data"):
            st.session_state.file_list = [pd.DataFrame()]

    if st.button("Generate PDF"):
        try:
            with st.spinner("Generating PDF..."):
                generate_pdf(st.session_state.agent)
            st.success("PDF Generated!")
            print_chat()
        except Exception as e:
            st.error(e)

    user_question = st.chat_input("Ask a question about your csv:")
    if user_question:
        try:
            with st.spinner("Thinking..."):
                handle_userinput(user_question, st.session_state.agent)
        except Exception as e:
            st.error(e)


if __name__ == "__main__":
    main()
