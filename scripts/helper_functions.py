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


import openai
import os
import streamlit as st
import pandas as pd
from pandasai import Agent, SmartDataframe
from pandasai.prompts import GeneratePythonCodePrompt
from pandasai.responses.streamlit_response import StreamlitResponse
from templates import prompt_template
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, Table, TableStyle


class FriendlyPrompt(GeneratePythonCodePrompt):
    template = prompt_template


def check_openai_key():
    """
    Check if the OpenAI key is present in environment variables
    """
    return os.getenv("OPENAI_API_KEY")


def generate_agent(llm, state):
    """
    Generates an agent for the user to interact with.

    Args:
        llm (OpenAI): An OpenAI object.
        state (SessionState): A Streamlit SessionState object.
    Returns:
        Agent: A PandasAI Agent object.
    """

    return Agent(
        state.file_list,
        config={
            "llm": llm,
            "verbose": True,
            "response_parser": StreamlitResponse,
            "custom_prompts": {"generate_python_code": FriendlyPrompt()},
            "custom_whitelisted_dependencies": ["random", "os"],
        },
        memory_size=5,
    )


def generate_pdf(state, selected_history):
    """
    Generates a PDF report from the chat history.

    Sends the user questions to OpenAI to create headers for each section of the report.
    Formats tables appropriately to fit page size.

    Args:
        state (SessionState): A Streamlit SessionState object.
        selected_history (list): The selected list of chat messages.

    Returns:
        None
    """
    if not selected_history:
        st.warning("Please select at least one message.")
        return

    doc = SimpleDocTemplate("report.pdf", pagesize=letter, title="Analysis")
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        "CustomStyle",
        parent=styles["Normal"],
        spaceAfter=12,
    )

    content = []
    selected_history = [message.split("\n") for message in selected_history]
    selected_history = [item for sublist in selected_history for item in sublist]
    prompt = f"Generate a concise title for this report in title case using the following information: {selected_history}"
    generate_heading(prompt, content, styles, size="Title")
    for i, message in enumerate(selected_history):
        if i % 2 == 0:
            prompt = f"""Rephrase this question into a concise heading in title case: {message}.
                If needed, the context for the request is {state.chat_history}. Ensure the heading is not a question."""
            generate_heading(prompt, content, styles)
        else:
            if isinstance(message, SmartDataframe):
                df = message
                data = [
                    df.columns[
                        :,
                    ].tolist()
                ] + df.values.tolist()
                colWidth = [580 // len(df.columns)] * len(df.columns)
                height_factor = 1.6
                rowHeights = [
                    max([len(str(cell)) for cell in row]) * height_factor
                    for row in data
                ]
                table_data = [
                    [
                        Paragraph(str(cell), getSampleStyleSheet()["BodyText"])
                        for cell in row
                    ]
                    for row in data
                ]
                t = Table(
                    table_data, colWidths=colWidth, rowHeights=rowHeights, splitByRow=1
                )
                t.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("INNERGRID", (0, 0), (-1, -1), 0.25, "black"),
                            ("BOX", (0, 0), (-1, -1), 0.25, "black"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("WORDWRAP", (0, 0), (-1, -1)),
                        ]
                    )
                )
                content.append(t)

            elif "img_" in str(message):
                content.append(
                    Image(message, width=400, height=400, kind="proportional")
                )

            else:
                content.append(Paragraph(message, custom_style))
    doc.build(content)
    st.success("PDF Generated!")


def generate_heading(prompt, content, styles, size="Heading3"):
    """
    Generates headings for each section of the report.

    Args:
        prompt (str): The prompt to send to OpenAI.
        content (list): The list of content to append to.
        styles (dict): The dictionary of styles.
        size (str): The size of the heading.

    Returns:
        None
    """

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}]
    )
    content.append(Paragraph(completion.choices[0].message.content, styles[size]))


def handle_userinput(user_question, state):
    """
    Handles user input and sends it to the agent, updates chat history with Q&A.

    Args:
        user_question (str): The user's question.
        state (SessionState): A Streamlit SessionState object.

    Returns:
        None
    """
    if state.file_list == [pd.DataFrame()]:
        st.write("Please load a CSV file first.")
        return
    if "chart" or "graph" or "plot" or "histogram" in user_question.lower():
        response = state.agent.chat(user_question, output_type="string")
    elif "table" in user_question.lower():
        response = state.agent.chat(user_question, output_type="dataframe")
    else:
        response = state.agent.chat(user_question)
    state.chat_history.append(f"{user_question} ;; {response}")


def print_chat(chat_history):
    """
    Prints the chat history to the screen.

    Args:
        chat_history (list): The list of chat messages.

    Returns:
        None
    """
    if not chat_history:
        return
    for message in chat_history:
        user_message = message.split(" ;; ")[0]
        assistant_message = message.split(" ;; ")[1]
        with st.chat_message("user"):
            st.write(user_message)

        with st.chat_message("assistant"):
            if "img_" in str(assistant_message):
                image = PILImage.open(assistant_message)
                st.image(image, use_column_width=True)
            else:
                st.write(assistant_message)


def validate_openai_key(key):
    """
    Validates the OpenAI key.

    Args:
        key (str): The OpenAI key.

    Returns:
        bool: True if valid, False otherwise.
    """
    if key is None:
        return False
    try:
        openai.api_key = key
        response = openai.Completion.create(
            engine="davinci", prompt="This is a test.", max_tokens=5
        )
        response.choices[0].text
        return True
    except:
        return False
