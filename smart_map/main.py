import streamlit as st
import pandas as pd
from io import StringIO
from langchain.chains import LLMChain, SequentialChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from smart_map.components.sidebar import sidebar

from smart_map.ui import (
    is_open_ai_key_valid,
    display_file_read_error,
)

from smart_map.core.caching import bootstrap_caching

EMBEDDING = "openai"
VECTOR_STORE = "faiss"
MODEL = "openai"

@st.cache_data
def load_template(template_file):
    temp_stringio = StringIO(template_file.getvalue().decode("utf-8"))
    template_string = temp_stringio.read()
    template_df = pd.read_csv(template_file)
    return template_string, template_df

# For testing
# EMBEDDING, VECTOR_STORE, MODEL = ["debug"] * 3

st.set_page_config(page_title="SmartMap", layout="wide")
st.header("SmartMap")

st.markdown(""" ###### SmartMap provides a streamlined solution for mapping data between tables using chatGPT. """)

# Enable caching for expensive functions
bootstrap_caching()

sidebar()

openai_api_key = st.session_state.get("OPENAI_API_KEY")

if not openai_api_key:
    st.warning(
        "Enter your OpenAI API key in the sidebar. You can get a key at"
        " https://platform.openai.com/account/api-keys."
    )
    
if 'template' not in st.session_state:
    st.session_state['template'] = []

if 'tableA' not in st.session_state:
    st.session_state['tableA'] = []
    
if 'chain_output' not in st.session_state:
    st.session_state['chain_output'] = []


template_file = st.file_uploader(
    "#### Upload the template table",
    type=["csv"],
    help="Please upload a csv file!",
)

if template_file:
    try:
        template_string, template_df = load_template(template_file)   
        st.session_state['template'].append(template_string)
    except Exception as e:
        display_file_read_error(e)
        
    with st.expander("Show template table"):
            # Hack to get around st.markdown rendering LaTeX
        st.write(template_df)

    # Upload the file to be converted to match the template

    upload_file = st.file_uploader(
        "Upload the table to be converted to the template format.",
        type=["csv"],
        help="Please upload a csv file!",
    )
    if upload_file:
        try:
            upload_string, upload_df = load_template(upload_file)
            st.session_state['tableA'].append(upload_string)
        except Exception as e:
            display_file_read_error(e)
            
        with st.expander("Show uploaded table"):
                # Hack to get around st.markdown rendering LaTeX
            st.write(upload_df)
            
        ### Create a prompt to send to openai containing the tables and instructions
        tables_prompt = f"""
            Here is the template table: \n
            {template_string}
            
            Here is the table (table A) to be mapped into the template schema: \n
            {upload_string}
            
            \n
            """

        print(tables_prompt)
        #### Send first prompt to openai
        if not is_open_ai_key_valid(openai_api_key):
            st.stop()

        llm = OpenAI(
                temperature=0.7, openai_api_key=openai_api_key, model_name="gpt-3.5-turbo"
            )

        memory = ConversationBufferMemory(memory_key="chat_history")

        if st.button("Begin Table Mapping", type="primary"):
            # Chain  1
            template = """Your task is to map a table that is formatted as a csv into the schema defined by a template\
            by transferring values and transforming values into the target format of the Template table.
            {tables}
            Extract information about the columns of the Template table and table A in the format of a text description. All of the data\
            is passed as text but if the text is numeric, describe the column data as numeric. 
            Format your response in markdown language using two tables. 
            The first table describes the template table where the first column contains the column name, the second contains the interpreted type of data, and the third gives a description of what that data appears to be.
            The second table describes the Table A where the first column contains the column name, the second contains the interpreted type of data, and the third gives a description of what that data appears to be.
        """
            prompt_template = PromptTemplate(input_variables=["tables"], template=template)
            initial_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="initial")

            # Chain 2
            template = """
            {initial}
            Your goal is to figure out the mapping between columns from the input table to the template table
            based on the column names and data value types, describe this mapping like a dictionary mapping.
            For each column in the template table, suggest columns from table A (1 or more relevant candidates), 
            showing the basis for the decision (formats, distributions, and other features that are highlighted in the backend).
            Format your response in markdown language as a table where the first column represents the template column, the second column\
                represents the column from Table A that is being mapped to the template column, and the third column explains the reasoning.
            """
            prompt_template = PromptTemplate(input_variables=["initial"], template=template)
            find_similar_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="find_similar")

            template = """
            {find_similar}
            Automatically generate data mapping code for each column display in the final Template format. 
            For example, for date columns, they may be in different formats, and it is necessary to change the order. 
            Define a new table to be mapped to called formatted_table that maps the appropriate columns from Table A (upload_df) with the correct naming convention from the template.
            Format your response in python language returning the complete, executable codeblock, and with each line of code described with a markdown comment.
            """
            prompt_template = PromptTemplate(input_variables=["find_similar"], template=template)
            data_mapping_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="mapping")
            
            template = """
            For the following code, return a function that takes a pandas dataframe and uses the specifed column mappings to return a properly formatted dataframe. Return only the executable python code:
            {mapping}
            """
            prompt_template = PromptTemplate(input_variables=["mapping"], template=template)
            code_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="code")
            
            overall_chain = SequentialChain(
                chains=[initial_chain, find_similar_chain, data_mapping_chain, code_chain],
                input_variables=["tables"],
                output_variables=["initial","find_similar","mapping", "code"],
                verbose=True,
            )
            with st.spinner(
                    "Generating Mapping"
                ):
                    chain_output = overall_chain(tables_prompt)
                    st.session_state.chain_output.append(chain_output)
            
            st.subheader("Table Description")
            st.markdown(chain_output["initial"])
            
            st.subheader("Compare Table Columns")
            st.markdown(chain_output["find_similar"])
            
            st.subheader("Code to Map to Template")
            st.markdown(chain_output["mapping"])
            
            
            # Verify and edit the generated code
            user_edit_code = st.text_area(
                label='Generated code',
                value=chain_output["code"],
                height=300,
                max_chars=None,
                key=None,
            )
            code_button = st.button("Run Code", type="primary")
            if code_button:
                try:
                    exec(user_edit_code)
                    st.success("Code executed successfully")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

                # Repeat for Table B
                upload_file_b = st.file_uploader(
                    "Upload the second table to be converted to the template format (Table B).",
                    type=["csv"],
                    help="Please upload a csv file!",
                )

                if upload_file_b:
                    up_stringio_b = StringIO(upload_file_b.getvalue().decode("utf-8"))
                    upload_string_b = up_stringio_b.read()
                    upload_df_b = pd.read_csv(upload_file_b)
                    tables_prompt_b = f"""
                    Here is the template table: \n
                    {template_string}
                    Here is the table (table B) to be mapped into the template schema: \n
                    {upload_string_b}
                    \n
                    """
                    st.subheader("Table Mapping for Table B")
                    st.markdown(sim_chain_seq.run(tables_prompt_b))

                    correct_mapping_b = st.button("The mapping for Table B is correct", type="primary")
                    if correct_mapping_b:
                        user_edit_code_b = st.text_area(
                            label='Generated code for Table B',
                            value=data_mapping_chain.run(tables_prompt_b),
                            height=300,
                            max_chars=None,
                            key=None,
                        )

                        if st.button("Run Code for Table B"):
                            try:
                                exec(user_edit_code_b)
                                st.success("Code executed successfully for Table B")
                            except Exception as e:
                                st.error(f"An error occurred: {e}")

