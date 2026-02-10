import duckdb
import csv
import pandas as pd

def fetch_wu03ew(residence):
    csv_src = 'data/wu03ew_v2.csv'

    con = duckdb.connect()

    # Get column names
    header = ["residence","workplace","all","home","metro","train","bus","taxi","motorcycle","driving","passenger","bicycle","foot","other"]

    # All columns are VARCHAR type
    schema = {col: "VARCHAR" for col in header}

    # Fetch all required data
    return con.execute(
        f"""SELECT * 
            FROM read_csv_auto('{csv_src}', columns={schema})
            WHERE residence = '{residence}'
        """
    ).fetchdf()

# Display all rows of the dataframe
pd.set_option('display.max_rows', None)

print(fetch_wu03ew('E02006106'))