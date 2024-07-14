import pandas as pd
import numpy as np
from scipy.stats import gaussian_kde
from concurrent.futures import ProcessPoolExecutor
from src.data_process.CPU_columnclassifier import categorize_columns
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

def analyze_csv(df, output_path, capping_info=None):
    # Read the shape of the dataframe
    shape = df.shape

    # Count the number of missing values and their percentage
    missing_values = df.isnull().sum()
    missing_percentage = (missing_values / len(df)) * 100
    missing_values = missing_values[missing_values > 0]
    missing_percentage = missing_percentage[missing_percentage > 0]
    
    # Write the results to the output file
    with open(output_path, 'w') as f:
        if missing_values.empty:
            f.write("Your Data is cleaned !!!\n")
            f.write("New Features added to your dataset\n")
            f.write("Loan Duration\n")
        else:
            f.write(f"Shape of the DataFrame: {shape}\n\n")
            f.write(f"{'Column Name':<28} | {'Missing Values':<15} | {'Missing Percentage':<5}\n")
            f.write(f"{'-'*28}-+-{'-'*15}-+-{'-'*5}\n")
            for column in missing_values.index:
                f.write(f"{column:<28} | {missing_values[column]:<15} | {missing_percentage[column]:<5.2f}%\n")
        
        # Add capping information if provided
        if capping_info:
            f.write("\nOutlier Capping Information:\n")
            for info in capping_info:
                f.write(f"{info}\n")
    # delete the dataframe to free up memory
    del df

def drop_col_row(df, datetime_columns):
    # Strip and lower case the column names
    df.columns = df.columns.str.strip().str.lower()
    datetime_columns = [col.lower().strip() for col in datetime_columns]
    
    # Drop columns with more than 40% missing values
    columns_dropped = []
    threshold = 0.4 * len(df)
    for column in df.columns:
        if df[column].isna().sum() >= threshold:
            columns_dropped.append(column)
            df.drop(column, axis=1, inplace=True)

    # take this column in the datetime columns if it is not in the datetime columns
    if 'agreement signing date' not in datetime_columns:
        datetime_columns.append('agreement signing date')

    # drop rows of mssing values in the datetime columns
    datetime_columns = [col for col in datetime_columns if col in df.columns]
    df.dropna(subset=datetime_columns, inplace=True)

    # drop duplicate rows
    df.drop_duplicates(inplace=True)
    # reset the index
    df.reset_index(drop=True, inplace=True)
    
    return df

def process_datetime_columns(df, datetime_columns):\
    # Convert the datetime columns to the date format
    for column in datetime_columns:
        df[column] = pd.to_datetime(df[column], format='%m/%d/%Y %I:%M:%S %p')
        df[column] = df[column].dt.strftime('%d/%m/%Y')
    return df

def kde_impute(df: pd.DataFrame, numeric_columns: list):
    # Apply KDE imputation for numeric columns
    for col in numeric_columns:
        data = df[col].dropna().values
        
        if len(data) == 0 or len(np.unique(data)) == 1:
            continue
        
        kde = gaussian_kde(data)
        missing_indices = df[col].isna()
        imputed_values = kde.resample(missing_indices.sum()).flatten()
        df.loc[missing_indices, col] = imputed_values
    
    return df

def fill_empty_values(df, columns_to_fill):
    # Fill missing values with 'Unknown'
    df[columns_to_fill] = df[columns_to_fill].fillna('Unknown')
    return df

def calculate_loan_duration(df):
    # Calculate loan duration in days, months, and years
    if not isinstance(df, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame")
    
    df.columns = df.columns.str.lower().str.strip()
    
    required_columns = ['end of period', 'agreement signing date']
    if not all(col in df.columns for col in required_columns):
        raise KeyError("Required columns for loan duration calculation are missing")
    
    for col in required_columns:
        temp_col = f'temp_{col}'
        if df[col].dtype != 'datetime64[ns]':
            df[temp_col] = pd.to_datetime(df[col], format='%d/%m/%Y')
        else:
            df[temp_col] = df[col]
    
    df['loan duration (days)'] = (df['temp_end of period'] - df['temp_agreement signing date']).dt.days
    df['loan duration (months)'] = ((df['temp_end of period'].dt.year - df['temp_agreement signing date'].dt.year) * 12 + 
                                    (df['temp_end of period'].dt.month - df['temp_agreement signing date'].dt.month))
    df['loan duration (years)'] = df['loan duration (days)'] / 365.25

    df = df.drop(columns=[f'temp_{col}' for col in required_columns])

    new_columns = ['loan duration (days)', 'loan duration (months)', 'loan duration (years)']
    existing_columns = [col for col in df.columns if col not in new_columns]
    df = df[new_columns + existing_columns]

    return df

def cap_outliers_iqr_with_zeros_pandas(df, numerical_columns):
    # Capping outliers using IQR
    capping_info = []
    for col in numerical_columns:
        non_zero_mask = (df[col] != 0) & (~df[col].isnull())
        non_zero_series = df.loc[non_zero_mask, col]

        if len(non_zero_series) > 0:
            Q1 = non_zero_series.quantile(0.25)
            Q3 = non_zero_series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            original_values = df[col].copy()
            df.loc[non_zero_mask, col] = df.loc[non_zero_mask, col].clip(lower=lower_bound, upper=upper_bound)
            outliers_capped = ((df[col] != original_values) & non_zero_mask).sum()
            capping_info.append(f"Handled {outliers_capped} outliers in column '{col}'.")
        else:
            capping_info.append(f"No non-zero values in column '{col}'. Skipping outlier handling.")

    return df, capping_info

def encode_categorical_columns(df, categorical_columns):
    # Create a copy of the dataframe to avoid modifying the original
    df_encoded = df.copy()

    for col in categorical_columns:
        unique_values = df[col].nunique()

        if unique_values > 20:
            # Use Label Encoding for columns with more than 20 unique values
            le = LabelEncoder()
            df_encoded[f'{col}_encoded'] = le.fit_transform(df[col].astype(str))
        else:
            # Use One-Hot Encoding for columns with 20 or fewer unique values
            ohe = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            encoded = ohe.fit_transform(df[[col]])
            encoded_df = pd.DataFrame(encoded, columns=[f'{col}_{cat}' for cat in ohe.categories_[0]])
            df_encoded = pd.concat([df_encoded, encoded_df], axis=1)

    return df_encoded

def process_chunk(chunk, datetime_columns, categorical_columns, id_columns):
    # Process each chunk in parallel
    chunk = process_datetime_columns(chunk, datetime_columns)
    chunk = fill_empty_values(chunk, categorical_columns + id_columns)
    chunk = calculate_loan_duration(chunk)
    return chunk

def preprocess_insights(input_path):
    # Read CSV file into a pandas DataFrame
    df = pd.read_csv(input_path, low_memory=False)
    
    # Generate the data report before preprocessing
    analyze_csv(df, 'src/insights_processed/before.txt')
    
    # Categorize columns
    column_types = categorize_columns(df)
    datetime_columns = column_types['datetime_columns']
    
    # Drop rows and columns
    df = drop_col_row(df, datetime_columns)
    
    # Categorise columns again after dropping column and rows
    column_types = categorize_columns(df)
    datetime_columns = column_types['datetime_columns']
    numeric_columns = column_types['numeric_columns']
    categorical_columns = column_types['categorical_columns']
    id_columns = column_types['id_columns']

    # Impute missing values using KDE for numeric columns
    df = kde_impute(df, numeric_columns)
    # Cap outliers using IQR
    df, capping_info = cap_outliers_iqr_with_zeros_pandas(df, numeric_columns)

    

    chunks = np.array_split(df, 10)  # Split DataFrame into chunks for parallel processing
    results = []
    
    # Process each chunk in parallel
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_chunk, chunk, datetime_columns, categorical_columns, id_columns) for chunk in chunks]
        for future in futures:
            results.append(future.result())

    # Concatenate the results
    df = pd.concat(results)
    
    # Drop the index column
    if 'unnamed: 0' in df.columns:
        df = df.drop(columns=['unnamed: 0'])

    # Generate the data report after preprocessing
    analyze_csv(df, 'src/insights_processed/after.txt', capping_info)

    # Encode categorical columns
    df = encode_categorical_columns(df, categorical_columns)

    return df
