import streamlit as st

from smart_map.components.faq import faq
from dotenv import load_dotenv
import os

load_dotenv()


def sidebar():
    with st.sidebar:
        st.markdown(
            "## How to use\n"
            "1. Enter your [OpenAI API key](https://platform.openai.com/account/api-keys) below🔑\n"  # noqa: E501
            "2. Upload a csv file with the template schema you would like to map to.📄\n"
            "3. Upload the csv file of the table you are mapping.\n"
        )
        api_key_input = st.text_input(
            "OpenAI API Key",
            type="password",
            placeholder="Paste your OpenAI API key here (sk-...)",
            help="You can get your API key from https://platform.openai.com/account/api-keys.",  # noqa: E501
            value=os.environ.get("OPENAI_API_KEY", None)
            or st.session_state.get("OPENAI_API_KEY", ""),
        )

        st.session_state["OPENAI_API_KEY"] = api_key_input

        st.markdown("---")
        st.markdown("# About")
        st.markdown(
            "SmartMap allows you to easily convert your tables into "
            "the desired schema as defined by a template. "
        )

        st.markdown("Made by Theo Mefford")
        st.markdown("---")

        faq()
