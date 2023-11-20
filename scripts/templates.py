css = """
<style>
.chat-message {
    padding: 1.5rem; border-radius: 0.5rem; margin-bottom: 1rem; display: flex
}
.chat-message.user {
    background-color: #2b313e
}
.chat-message.bot {
    background-color: #475063
}
.chat-message .avatar {
  width: 20%;
}
.chat-message .avatar img {
  max-width: 78px;
  max-height: 78px;
  border-radius: 50%;
  object-fit: cover;
}
.chat-message .message {
  width: 80%;
  padding: 0 1.5rem;
  color: #fff;
}
"""

bot_template = """
<div class="chat-message bot">
    <div class="avatar">
        <img src="https://i.ibb.co/cN0nmSj/Screenshot-2023-05-28-at-02-37-21.png" style="max-height: 78px; max-width: 78px; border-radius: 50%; object-fit: cover;">
    </div>
    <div class="message">{{MSG}}</div>
</div>
"""

user_template = """
<div class="chat-message user">
    <div class="avatar">
        <img src="https://i.ibb.co/rdZC7LZ/Photo-logo-1.png">
    </div>
    <div class="message">{{MSG}}</div>
</div>
"""

prompt_template = """
        You are provided with the following pandas DataFrames:

        {dataframes}

        <conversation>
        {conversation}
        </conversation>

        This is the initial python function. Do not change the params. Given the context, use the right dataframes.
        ```python
        {current_code}
        ```
        {skills}
        Take a deep breath and reason step-by-step. Act as a senior data analyst.
        In the answer, you must never write the "technical" names of the tables.
        You will be communicating with non-technical stakeholders, so ensure that all return types are full sentences
        unless the user is asking for a table or chart.

        If you are asked to create a chart, please ensure that the output is only a string giving the chart path.
        The chart path should not be a complete sentence. It should be in the ./charts directory. Do not output the chart itself.
        Each chart name should be img_ + a random number. Use numpy.random.rand() to generate the random number.

        If asked to produce a table, please output a dataframe, not a string! Do not display indicies.
        Please also format any headers to be title case.

        Based on the last message in the conversation:
        {reasoning}
"""
