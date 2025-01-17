import pyodbc
import sys
import os
from dotenv import load_dotenv
load_dotenv()

from doc_utils import *
from env_vars import *
import json
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, inspect
from sqlalchemy.dialects.mssql import NVARCHAR, INTEGER, FLOAT, DECIMAL
from sqlalchemy.schema import CreateTable
from sqlalchemy.sql import insert

import sqlalchemy


get_column_count_sql = """ 
SELECT COUNT(*)
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME = '{table_name}';
"""

get_row_count_sql = """
SELECT COUNT(*) AS NumberOfRows
FROM {table_name};
"""

delete_table_sql = """
DROP TABLE IF EXISTS {schema}.{table_name};
"""




class MSSqlManager:
    def __init__(self, 
                 server = f"{AZURE_SQL_SERVER_NAME}.database.windows.net", 
                 database = AZURE_SQL_DATABASE_NAME, 
                 username = AZURE_SQL_USERNAME, 
                 password = AZURE_SQL_PASSWORD, 
                 schema_name = AZURE_SQL_SCHEMA_NAME,
                 driver = AZURE_SQL_DRIVER,):

        self.server = server
        self.database = database
        self.username = username
        self.password = password
        self.driver = driver
        self.schema_name = schema_name

        self.engine = create_engine(f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}', echo=False)

        self.numerical_cols = []


    # Function to map pandas data types to SQL Server data types and determine max length for strings
    def dtype_mapper(self, col_name, dtype):
        if "int" in dtype.name:
            print(f"{col_name} is INT")
            self.numerical_cols.append(col_name)
            return INTEGER()
        elif "float" in dtype.name:
            print(f"{col_name} is float")
            self.numerical_cols.append(col_name)
            return DECIMAL(precision=18, scale=6)
        elif "object" in dtype.name:  # Assuming object dtype are strings
            # Calculate the maximum string length in the column
            max_length = df[col_name].dropna().astype(str).map(len).max()
            # Ensure there is a default length if all values are NaN or the column is empty
            if pd.isna(max_length):
                max_length = 10
            return NVARCHAR(length=int(max_length))
        else:
            # Default case for any other types detected
            return NVARCHAR(length=1024)


    # Function to detect file type and read the first few records into a DataFrame
    def read_data_file(self, file_path, skiprows=0):
        file_path = file_path.lower()
        if file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, skiprows=skiprows)
        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, skiprows=skiprows)
        else:
            raise ValueError("Unsupported file type")

        df = df.dropna(how='all', axis=1)
        print(f"Read df with {len(df.columns)} columns and {len(df)} rows")
        return df 


    def create_table(self, df, table_name, load_table=True):
        # Use the metadata from SQLAlchemy to construct the CREATE TABLE statement
        metadata = MetaData()
        table = Table(table_name, metadata, *[Column(col, self.dtype_mapper(col, df.dtypes[col])) for col in df.columns], schema=self.schema_name)

        # Create the table in the database
        try:
            metadata.create_all(self.engine)
            print(f"Creating Table Operation Successul")
        except Exception as e:
            print(f"Creating Table Operation Unsuccessful.\nException:\n{e}")

        if load_table: self.insert_df_rows(df, table)

        return table


    def insert_df_rows(self, df, table):
        try:
            # Insert DataFrame data into the table
            with self.engine.connect() as connection:
                i = 0
                for index, row in df.iterrows():
                    # Create a dictionary of column names and values for the row to be inserted
                    data = {col: (None if pd.isna(row[col]) else row[col]) for col in df.columns}
                    # Perform the insert operation
                    connection.execute(table.insert(), data)
                    connection.commit()
                    if (i % 10) == 0: print(f"Inserted {i} rows successfully")
                    i += 1
            print(f"Inserting data into Table Operation Successul")
        except Exception as e:
            print(f"Inserting data into Table Operation Unsuccessful.\nException:\n{e}")


    def get_column_count(self, table_name):
        sql_statement = get_column_count_sql.format(table_name=table_name)
        return self.execute_sql(sql_statement)
    
    
    def get_row_count(self, table_name):
        sql_statement = get_row_count_sql.format(table_name=table_name)
        return self.execute_sql(sql_statement)

    def drop_table(self, table_name):
        sql_statement = delete_table_sql.format(table_name=table_name, schema = self.schema_name)
        return self.execute_sql(sql_statement)


    def execute_sql(self, sql_command):
        try:
            sql_command = sqlalchemy.text(sql_command)
            with self.engine.connect() as connection:
                result = connection.execute(sql_command).fetchall()
                print(f"Success in executing sql command:\n{sql_command}\n")
                return result
        except Exception as e:
            print(f"Exception in executing sql command:\n{sql_command}\n\nException:\n{e}")






