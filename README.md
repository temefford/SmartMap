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

