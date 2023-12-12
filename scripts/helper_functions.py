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


def generate_pdf(state):
    """
    Generates a PDF report from the chat history.

    Sends the user questions to OpenAI to create headers for each section of the report.
    Formats tables appropriately to fit page size.

    Args:
        state (SessionState): A Streamlit SessionState object.

    Returns:
        None
    """
    doc = SimpleDocTemplate("report.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    custom_style = ParagraphStyle(
        "CustomStyle",
        parent=styles["Normal"],
        spaceAfter=12,
    )

    content = []
    prompt = f"Generate a title for this report in title case using the following information: {state.chat_history}"
    generate_heading(prompt, content, styles, size="Title")
    for i, message in enumerate(state.chat_history):
        if i % 2 == 0:
            prompt = f"Rephrase this question into a concise heading in title case: {message}. Ensure the heading is not a question."
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
                content.append(Image(message, width=400, height=400))

            else:
                content.append(Paragraph(message, custom_style))
    doc.build(content)


def generate_heading(prompt, content, styles, size="Heading2"):
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
    state.chat_history.append(user_question)
    state.chat_history.append(response)
    print_chat(state.chat_history)


def print_chat(chat_history):
    """
    Prints the chat history to the screen.

    Args:
        chat_history (list): The list of chat messages.

    Returns:
        None
    """
    for i, message in enumerate(chat_history):
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
