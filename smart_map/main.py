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

st.markdown(""" ###### SmartMap provides a streamlined solution for data standarization by mapping data tables to the desired schema using chatGPT. """)

# Enable caching for expensive functions
bootstrap_caching()

sidebar()

openai_api_key = st.secrets["OPENAI_API_KEY"]
#openai_api_key = 

# if not openai_api_key:
#     st.warning(
#         "Enter your OpenAI API key in the sidebar. You can get a key at"
#         " https://platform.openai.com/account/api-keys."
#     )

    
if 'chain_output' not in st.session_state:
    st.session_state['chain_output'] = []

if 'chain_b_output' not in st.session_state:
    st.session_state['chain_b_output'] = []

if 'code_runs' not in st.session_state:
    st.session_state['code_runs'] = False

if 'conv_code' not in st.session_state:
    st.session_state['conv_code'] = False

if 'overall_chain' not in st.session_state:
    st.session_state['overall_chain'] = False

if 'overall_b_chain' not in st.session_state:
    st.session_state['overall_b_chain'] = False

if 'table_b' not in st.session_state:
    st.session_state['table_b'] = False


def create_chains():
    llm = OpenAI(
            temperature=0.1, openai_api_key=openai_api_key, model_name=st.session_state.model
        )
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
    Here are the tables we are using to create a mapping function from the example (Table A) to the template schema (tempate):
    {tables}
    Here is a description of the tables:
    {initial}
    Your goal is to figure out the mapping between columns from the input table to the template table
    based on the column names and data value types, describe this mapping like a dictionary mapping.
    For each column in the template table, suggest columns from table A (1 or more relevant candidates), 
    showing the basis for the decision (formats, distributions, and other features that are highlighted in the backend).
    If more than 1 column can map from table A to the template, include both as other tables that use this mapping may have either of the possible columns.
    Format your response in markdown language as a table where the first column represents the template column, the second column\
        represents the column from Table A that is being mapped to the template column, and the third column explains the reasoning.
        
    """
    prompt_template = PromptTemplate(input_variables=["tables","initial"], template=template)
    find_similar_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="find_similar")

    template = """
    Here are the tables we are using to create a mapping function from the example (Table A) to the template schema (tempate):
    {tables}
    Here is a description of the tables:
    {initial}
    and here are the projected column-column pairs:
    {find_similar}
    For each of the columns that is mapped from A to the template, does the value of A match that of the value for the corresponding row in template?
    Does any transformation need to be applied to make the value match, such as changing the style of the datetime? Are there differences in characters, such as dashes, - , that need to be removed?

    For text data columns like policy, do you need to remove a hyphen, -, to make the columns match?
    Do you need to reformat data columns to match?
    """
    prompt_template = PromptTemplate(input_variables=["tables","initial","find_similar"], template=template)
    data_mapping_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="mapping")

    template = """
    Here are the tables we are using to create a mapping function from the example (Table A) to the template schema (tempate):
    {tables}
    Here is a description of the tables:
    {initial}
    and here are the original column-column pairs to match from Table A to template schema:
    {mapping}

    Automatically generate data mapping code for each column display in the final Template format. 
    For example, for date columns, they may be in different formats, and it is necessary to change the order. 
    If more than one column maps from Table A to the template table column, create a dynamic mapping that can convert either without running into an error.
    Define a function that maps an input table that has schema similar to Table A (upload_df) to schema of template, with the correct naming convention from the template.
    Format your response in python language returning the complete, executable codeblock, and with each line of code described with a markdown comment.
    Only provide the mapping for relevant to the columns in the template but make it dynamic to account for potential alternative columns.
    There should be no code to map to a column that is not in the template table.
    Be sure to perform the necessary data manipulation on column values to make the values of table A match the format of the template, such as reformatting date and removing hyphens.
    """
    prompt_template = PromptTemplate(input_variables=["tables","initial","mapping"], template=template)
    mapping_code_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="mapping_code")
    
    template = """
    {tables}
    For the following code, return a function that takes a pandas dataframe and uses the specifed column mappings to return a properly formatted dataframe. Return only the executable python code.
    Do not include any single quotes or reference, return just the code that can be copy-pasted into python.
    Be sure to include transformation steps: 
    1. reformatting date column in necessary
    2. removing "-" from string data to make columns match template. Specifically, remove from the PolicyNumber column.
    {mapping}
    Here is the code:
    {mapping_code}

    Do not include any unnecessary lines like ('''python) and do not return any examples. Only return the function that takes a table and converts it to the desired schema.
    Make sure that the code maps the appropriate columns and values from Table A to the template. If the code does not, either fix it or report an issue.
    """
    prompt_template = PromptTemplate(input_variables=["tables", "mapping", "mapping_code"], template=template)
    code_chain = LLMChain(llm=llm, prompt=prompt_template, output_key="code")
    
    overall_chain = SequentialChain(
                        chains=[initial_chain, find_similar_chain, data_mapping_chain, mapping_code_chain, code_chain],
                        input_variables=["tables"],
                        output_variables=["initial","find_similar","mapping","mapping_code","code"],
                        verbose=True,
                    )
    return overall_chain


def create_function_from_string(func_string):
    """
    Create a function from a string.

    Parameters:
        func_string (str): A string representation of a Python function.

    Returns:
        function: A callable Python function.
    """
    # Use exec to define the function
    exec(func_string, globals())

    # Extract the function name from the string
    func_name = func_string.split("(")[0].split()[-1]

    # Return the function
    return globals()[func_name]



def main():

    # container for uploading tables
    upload_container = st.container()
    with upload_container:
        template_file = st.file_uploader(
            "#### Upload the template table",
            type=["csv"],
            help="Please upload a csv file!",
        )

        if template_file:
            try:
                template_string, template_df = load_template(template_file)   
                st.session_state['template']=template_string
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
                    st.session_state['tableA']=upload_string
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
                #### Send first prompt to openai
                if not is_open_ai_key_valid(openai_api_key):
                    st.stop()
               
                if st.button("Begin Table Mapping", type="primary"):
                    overall_chain = create_chains()
                    st.session_state.overall_chain=overall_chain
                    with st.spinner(
                            "Generating Mapping"
                        ):
                            chain_output = overall_chain(tables_prompt)
                            st.session_state.chain_output=chain_output
                    
    with st.container():
        if st.session_state.chain_output:
            st.subheader("Table Description")
            st.markdown(st.session_state.chain_output["initial"])
            
            st.subheader("Compare Table Columns")
            st.markdown(st.session_state.chain_output["find_similar"])
            
            st.subheader("Map to Template")
            st.markdown(st.session_state.chain_output["mapping"])

            st.subheader("Code to Map to Template")
            st.markdown(st.session_state.chain_output["mapping_code"])
    
    with st.container():
        if st.session_state.chain_output:
            st.subheader("Python Code for Table Conversion")
            st.markdown("Below is the code that will map your data table into the schema matching the template. Please review, make any desired modifications, and click run to confirm that the code exectutes.")
            # Verify and edit the generated code
            user_edit_code = st.text_area(
                label='Generated code',
                value=st.session_state.chain_output["code"],
                height=300,
                max_chars=None,
                key=None,
            )
            code_button = st.button("Run Code", type="primary")
            if code_button:
                st.session_state.chain_output["code"] = user_edit_code
                try:
                    exec(user_edit_code)
                    st.success("Code executed successfully")
                    st.session_state.code_runs=True
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                
                convert_table_func = create_function_from_string(user_edit_code)

                table_a_conv = convert_table_func(upload_df)   
                st.session_state.convert_function = convert_table_func
                with st.expander("Show converted table"):
                    st.write(table_a_conv)
                with st.expander("Show Table A table"):
                    st.write(upload_df)
                
                st.download_button(
                "Press to Download",
                table_a_conv.to_csv(index=False).encode('utf-8'),
                "table_a.csv",
                "",
                key='download-csv'
                )

    with st.container():
        if st.session_state.code_runs:         
            st.subheader("Convert another table")    
            # Repeat for Table B
            upload_file_b = st.file_uploader(
                "Upload the second table to be converted to the template format (Table B).",
                type=["csv"],
                help="Please upload a csv file!",
            )
            if upload_file_b:
                try:
                    upload_string_b, upload_df_b = load_template(upload_file_b)
                    st.session_state['table_b']=upload_string_b
                except Exception as e:
                    display_file_read_error(e)
                tables_b_prompt = f"""
                            Here is the template table: \n
                            {template_string}
                            
                            Here is the table (table B) to be mapped into the template schema: \n
                            {st.session_state.table_b}
                            \n
                            """
                if st.button("Begin Table Mapping:", type="primary"):
                    b_chain = create_chains()
                    st.session_state.overall_b_chain=b_chain
                    with st.spinner(
                            "Generating Mapping"
                        ):
                            chain_output = b_chain(tables_b_prompt)
                            st.session_state.chain_b_output=chain_output

    with st.container():
        if st.session_state.chain_b_output:
            st.subheader("Python Code for Table B Conversion")
            st.markdown("Below is the code that will map your data table into the schema matching the template. Please review, make any desired modifications, and click run to confirm that the code exectutes.")
            # Verify and edit the generated code
            user_edit_code = st.text_area(
                label='Generated code',
                value=st.session_state.chain_b_output["code"],
                height=300,
                max_chars=None,
                key=None,
            )
            code_b_button = st.button("Run Code for B", type="primary")
            if code_b_button:
                st.session_state.chain_b_output["code"] = user_edit_code
                try:
                    exec(user_edit_code)
                    st.success("Code executed successfully")
                    st.session_state.code_runs=True
                except Exception as e:
                    st.error(f"An error occurred: {e}")
                
                convert_table_func = create_function_from_string(user_edit_code)

                table_b_conv = convert_table_func(upload_df_b)   
                st.session_state.convert_function = convert_table_func
                with st.expander("Show reformatted Table B"):
                    st.write(table_b_conv)
                with st.expander("Show original Table B table"):
                    st.write(upload_df_b)
                st.download_button(
                "Press to Download",
                table_b_conv.to_csv(index=False).encode('utf-8'),
                "table_b.csv",
                "",
                key='download-csv'
                )

if __name__ == "__main__":
    main()

