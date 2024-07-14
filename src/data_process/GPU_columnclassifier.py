import cudf
from dateutil import parser

def categorize_columns_gpu(df):
    # Read first 10 rows of the dataframe
    df = df.head(10)
    # Initialize empty lists for datetime, numeric, categorical, and id columns
    datetime_columns = []
    numeric_columns = []
    categorical_columns = []
    id_columns = []

    def is_date(string):
        try:
            # Attempt to parse the string as a date
            parser.parse(string, fuzzy=False)
            # if successful, return True
            return True
        except (ValueError, TypeError):
            # if not, return False
            return False

    def is_categorical(column):
        # Remove NaN values and convert to string
        non_na_values = column.dropna().astype(str)

        # Check if there are any non-NaN values and if there are fewer unique values than total values
        if len(non_na_values) > 0 and non_na_values.nunique() < len(non_na_values):
            return True
        
        # If not categorical by the above check, return True if it's not numeric
        return not cudf.api.types.is_numeric_dtype(column)

    def is_id_column(col_name, column):
        # Calculate the ratio of unique values to total values in the column
        unique_ratio = column.nunique() / len(column)

        # List of common keywords found in ID column names
        id_keywords = ['id', 'identifier', 'key', 'code', 'number', 'no', 'num', 'project']

        # Return True if any of the following conditions are met:
        return (any(keyword in col_name.lower() for keyword in id_keywords) and unique_ratio > 0.7) or unique_ratio > 0.95 or col_name.lower() in ['project id', 'loan number']

    def process_column(col):

        # Remove NaN values and convert to string
        non_na_values = df[col].dropna()

        # Check if the column is an ID column
        if is_id_column(col, df[col]):
            return 'id', col
        
        # Check if the column is a datetime column
        elif cudf.api.types.is_float_dtype(df[col]) or cudf.api.types.is_integer_dtype(df[col]):
            return 'numeric', col
        
        # Check if the column contains date values
        elif all(is_date(str(item)) for item in non_na_values.head(100).to_pandas()) and not cudf.api.types.is_numeric_dtype(df[col]):
            return 'datetime', col
        
        # Check if the column is a categorical column
        elif is_categorical(df[col]):
            return 'categorical', col
        return None, col

    # Iterate over the columns in the dataframe
    for col in df.columns:
        category, col_name = process_column(col)
        if category == 'datetime':
            datetime_columns.append(col_name)
        elif category == 'numeric':
            numeric_columns.append(col_name)
        elif category == 'id':
            id_columns.append(col_name)
        elif category == 'categorical':
            categorical_columns.append(col_name)
    
    # Return a dictionary containing categorized column lists
    return {
        'datetime_columns': datetime_columns,
        'numeric_columns': numeric_columns,
        'categorical_columns': categorical_columns,
        'id_columns': id_columns
    }
