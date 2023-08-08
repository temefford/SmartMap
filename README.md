<h1 align="center">
SmartMap
</h1>

https://smartmap.streamlit.app/

SmartMap provides a streamlined solution for mapping data between tables using chatGPT.

## Steps

1. Upload a csv file with the template schema you would like to map to.
2. Upload the csv file of the table you are mapping."
3. Click button and let the system figure out how to transform to the correct format.
4. Upload another table to be mapped

## 💻 Running Locally

1. Clone the repository📂

```bash
git clone https://github.com/temefford/SmartMap
cd SmartMap
```

2. Install dependencies with [Poetry](https://python-poetry.org/) and activate virtual environment🔨

```bash
poetry install
poetry shell
```

3. Run the Streamlit server🚀

```bash
cd smart_map
streamlit run main.py
```


### Some edge cases and potential solutions:
#### 1. **Similar Column Names but Different Data**:
If two columns have similar names, the algorithm might wrongly map them even if they contain different kinds of data.

**Solution**: Instead of just looking at column names, also consider the data types, sample data from each column, and data distributions to make more accurate mappings.

#### 2. **Different Value Representations**:
Consider a date column. One table might represent dates as "dd-mm-yyyy" while another might use "mm/dd/yy".

**Solution**: Implement type inference mechanisms to detect such discrepancies in data representation. Use pattern recognition to identify common data formats and convert data into a standardized format before mapping.

#### 3. **Large Tables with Numerous Columns**:
For tables with a large number of columns, the process might become slow or the AI might time out.

**Solution**: Chunk the process. Instead of processing the entire table at once, process it in chunks. Also, the use of efficient algorithms and data structures can improve speed.

### 4. **Inconsistent Data**:
In some columns, especially in manually filled tables, the data can be inconsistent (e.g., mixing text with numbers in a supposedly numeric column).

**Solution**: Clean the data before processing. Identify and handle outliers or inconsistent entries, possibly using predefined rules or by inferring the correct type from the majority of the data in the column.

### 5. **Ambiguous Matches**:
Multiple columns in the input table might be good matches for a single column in the template.

**Solution**: Instead of making a final decision, provide the user with suggestions and allow them to choose the best fit. Use user feedback to improve future suggestions.

#### 6. **Loss of Information**:
Some columns might be ignored if they don't have an apparent match in the template.

**Solution**: Always provide a review step for the user. Highlight the columns that weren't mapped and give users an option to manually map or store them as metadata.

### 7. **Historical Biases**:
Relying too heavily on historical transformations can introduce biases, especially if past mappings contained errors or if the template has evolved over time.

**Solution**: Regularly update the training data and allow users to provide feedback on mappings. Ensure that the system can adapt to new mapping patterns and isn't stuck in outdated methodologies.

### 8. **Retraining on Synthetic Data**:
Synthetic data might not always capture the complexities of real-world data.

**Solution**: While synthetic data is useful for expanding the dataset, it's essential to balance it with real-world examples. Use synthetic data to cover edge cases, but ensure the model is primarily trained on actual mapping scenarios.

#### 9. **Complex Transformations**:
Some transformations aren't straightforward column-to-column mappings but require more complex operations, such as merging or splitting columns.

**Solution**: Build functionality to detect such requirements. For example, if there's a "full name" column in the input but separate "first name" and "last name" columns in the template, the tool should recognize this and offer to split the column.

In essence, while automating the mapping process can save time and reduce errors, human oversight is invaluable, especially in the early stages. As the system learns from more real-world scenarios and user feedback, its accuracy and efficiency will improve over time.
