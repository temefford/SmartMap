# flake8: noqa
import streamlit as st


def faq():
    st.markdown(
        """
## How does SmartMap work?
Introducing "SmartMap", an intelligent data mapping tool designed to revolutionize your data standardization workflow. In the complex data landscape of modern businesses, managing and harmonizing data from various sources can be a cumbersome task. SmartMap is here to alleviate this pain, providing a streamlined solution for mapping data between tables, even when they have differing column names, value formats, or irrelevant columns.

Leveraging the power of cutting-edge Language Learning Models (LLM), SmartMap takes your input tables and a specified template to smartly map and transform data, ensuring uniformity and compliance with your desired format. Whether you are dealing with employee health insurance tables or other financial data, SmartMap will seamlessly transfer values from your source tables to your target template, all while transforming them into the appropriate format.

SmartMap is not just an automated tool; it's a collaborative partner. In cases of ambiguity, it invites you to make the best choice from suggested mappings, ensuring human judgement is valued. Additionally, it generates transformation code, allowing you to review, edit, and customize it as necessary.

Beyond mapping and transforming, SmartMap provides robust validation, alerting you of any discrepancies between your newly transformed data and the target template. Data accuracy and integrity are guaranteed, making SmartMap an indispensable tool in your financial toolkit. 

Take the guesswork out of data mapping with SmartMap, your smart assistant in managing complex financial data.
"""
    )
