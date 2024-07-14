import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from joblib import load
from sklearn.preprocessing import LabelEncoder
import io
import sys
import os
import scipy.stats as stats
import gc

def safe_plot_save(fig, filename, output_path):
    # Save the plot to the output directory
    try:
        fig.savefig(os.path.join(output_path, filename))
        plt.close(fig)
    except Exception as e:
        print(f"Error saving plot {filename}: {str(e)}")

def capture_output(func):
    # Capture the output of the function and return it as a string
    def wrapper(*args, **kwargs):
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        func(*args, **kwargs)
        sys.stdout = old_stdout
        return new_stdout.getvalue()
    return wrapper

def generate_insights(df, output_file_path):
    # Create output directory if it doesn't exist
    os.makedirs(output_file_path, exist_ok=True)

    output = "Starting insight generation...\n"

    # Preprocess data
    categorical_columns = df.select_dtypes(include=['object']).columns
    label_encoders = {}
    
    for col in categorical_columns:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        label_encoders[col] = le

    model_path = 'models'

    # Regional distribution insight (doesn't use any model)
    output += regional_distribution_insight(df, label_encoders, output_file_path)

    # Loan status insight
    loan_status_model = load(os.path.join(model_path, 'loan_status_rf_model.joblib'), mmap_mode='r')
    output += loan_status_insight(df, loan_status_model, label_encoders, output_file_path)
    del loan_status_model
    gc.collect()

    # Interest rate insight
    interest_rate_model = load(os.path.join(model_path, 'interest_rate_rf_model.joblib'), mmap_mode='r')
    output += interest_rate_insight(df, interest_rate_model, output_file_path)
    del interest_rate_model
    gc.collect()

    # Disbursed amount insight
    disbursed_amount_model = load(os.path.join(model_path, 'disbursed_amount_rf_model.joblib'), mmap_mode='r')
    output += disbursed_amount_insight(df, disbursed_amount_model, output_file_path)
    del disbursed_amount_model
    gc.collect()

    output += "Insight generation completed.\n"
    return output


# Generates insights of the regional distribution
@capture_output
def regional_distribution_insight(df, label_encoders, output_file_path):

    if 'region' not in df.columns or 'disbursed amount' not in df.columns:
        print("Error: 'region' or 'disbursed amount' column not found in the dataset.")
        return

    df['region'] = label_encoders['region'].inverse_transform(df['region'])
    regional_distribution = df.groupby('region')['disbursed amount'].sum().sort_values(ascending=False)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    regional_distribution.plot(kind='bar', ax=ax)
    ax.set_title('Regional Distribution of Loans (Disbursed Amount)')
    ax.set_xlabel('Region')
    ax.set_ylabel('Total Disbursed Amount')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    safe_plot_save(fig, 'regional_distribution.png', output_file_path)
    
    print("\nRegional Distribution Insight:")
    print(regional_distribution)
    if not regional_distribution.empty:
        print(f"\nInsight: The region with the highest total disbursed amount is {regional_distribution.index[0]}")
        print("This information can help in prioritizing regions for future investments.")
    else:
        print("No data available for regional distribution.")

    
# Generates insights of the loan status
@capture_output
def loan_status_insight(df, model, label_encoders, output_file_path):
    required_columns = set(model.feature_names_in_)
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        print(f"Error: The following required columns are missing from the dataset: {missing_columns}")
        return

    X = df[model.feature_names_in_]
    
    try:
        predicted_status = model.predict(X)
        predicted_status = label_encoders['loan status'].inverse_transform(predicted_status)
        status_distribution = pd.Series(predicted_status).value_counts()
        
        fig, ax = plt.subplots(figsize=(12, 5))

        total_count = status_distribution.sum()
        percentages = status_distribution / total_count

        # Group small slices into 'Other'
        other_mask = percentages < 0.02
        if other_mask.any():
            other_count = status_distribution[other_mask].sum()
            status_distribution = status_distribution[~other_mask]
            status_distribution['Other'] = other_count

        percentages = status_distribution / status_distribution.sum()
        show_numbers = not all(abs(p - percentages.mean()) < 0.05 for p in percentages)

        wedges, texts, autotexts = ax.pie(status_distribution, 
                                        labels=status_distribution.index if not show_numbers else None,
                                        autopct='%1.1f%%' if show_numbers else None, 
                                        startangle=90, 
                                        textprops=dict(color="w"), 
                                        pctdistance=0.85,
                                        wedgeprops=dict(width=0.4))

        ax.axis('equal')
        if show_numbers:
            ax.legend(status_distribution.index, title="Loan Status", loc="center", bbox_to_anchor=(1, 0, 0.5, 1))
        ax.set_title('Distribution of Predicted Loan Statuses', fontsize=30)

        plt.tight_layout()
        safe_plot_save(fig, 'loan_status_distribution.png', output_file_path)
        
        print("\nLoan Status Distribution Insight:")
        print(status_distribution)
        if not status_distribution.empty:
            print(f"\nInsight: The most common predicted loan status is {status_distribution.index[0]}")
            print("This distribution helps in understanding the overall health of the loan portfolio.")
        else:
            print("No data available for loan status distribution.")
    except Exception as e:
        print(f"Error in loan status prediction: {str(e)}")


# Generates insights of the interest rate
@capture_output
def interest_rate_insight(df, model, output_file_path):
    required_columns = set(model.feature_names_in_)
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        print(f"Error: The following required columns are missing from the dataset: {missing_columns}")
        return

    X = df[model.feature_names_in_]
    
    try:
        predicted_rates = model.predict(X)
        
        fig = plt.figure(figsize=(12, 10))
        gs = fig.add_gridspec(3, 3)
        ax_main = fig.add_subplot(gs[1:, :2])
        ax_right = fig.add_subplot(gs[1:, 2], sharey=ax_main)
        ax_top = fig.add_subplot(gs[0, :2], sharex=ax_main)

        hb = ax_main.hexbin(df['loan duration (years)'], predicted_rates, gridsize=20, cmap='YlOrRd')
        cb = fig.colorbar(hb, ax=ax_main, label='Count')

        sample_size = min(1000, len(df))
        sample_indices = np.random.choice(len(df), sample_size, replace=False)
        ax_main.scatter(df['loan duration (years)'].iloc[sample_indices], 
                        predicted_rates[sample_indices], 
                        alpha=0.3, color='blue', s=5)

        z = np.polyfit(df['loan duration (years)'], predicted_rates, 1)
        p = np.poly1d(z)
        ax_main.plot(df['loan duration (years)'], p(df['loan duration (years)']), "r--", alpha=0.8)

        ax_right.hist(predicted_rates, bins=50, orientation='horizontal', alpha=0.5)
        ax_top.hist(df['loan duration (years)'], bins=50, alpha=0.5)

        ax_main.set_xlabel('Loan Duration (Years)')
        ax_main.set_ylabel('Predicted Interest Rate')
        ax_right.set_xlabel('Count')
        ax_top.set_ylabel('Count')

        plt.suptitle('Interest Rate Analysis: Relationship with Loan Duration')
        plt.tight_layout()
        safe_plot_save(fig, 'interest_rate_analysis.png', output_file_path)
        
        print("\nInterest Rate Analysis Insight:")
        print("Average predicted interest rate:", np.mean(predicted_rates))
        correlation = stats.pearsonr(df['loan duration (years)'], predicted_rates)[0]
        print(f"Correlation between loan duration and predicted interest rate: {correlation:.4f}")
        print("\nInsight: There appears to be a relationship between loan duration and interest rates.")
        print("This information can guide financial planning and borrowing decisions.")
    except Exception as e:
        print(f"Error in interest rate prediction: {str(e)}")



# Generates insights of the disbursed amount
@capture_output
def disbursed_amount_insight(df, model, output_file_path):
    required_columns = set(model.feature_names_in_)
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        print(f"Error: The following required columns are missing from the dataset: {missing_columns}")
        return

    X = df[model.feature_names_in_]
    
    try:
        predicted_amounts = model.predict(X)
        
        fig = plt.figure(figsize=(12, 10))
        gs = fig.add_gridspec(3, 3)
        ax_main = fig.add_subplot(gs[1:, :2])
        ax_right = fig.add_subplot(gs[1:, 2], sharey=ax_main)
        ax_top = fig.add_subplot(gs[0, :2], sharex=ax_main)

        hb = ax_main.hexbin(df['original principal amount'], predicted_amounts, gridsize=20, cmap='YlOrRd')
        cb = fig.colorbar(hb, ax=ax_main, label='Count')

        sample_size = min(1000, len(df))
        sample_indices = np.random.choice(len(df), sample_size, replace=False)
        ax_main.scatter(df['original principal amount'].iloc[sample_indices], 
                        predicted_amounts[sample_indices], 
                        alpha=0.3, color='blue', s=5)

        z = np.polyfit(df['original principal amount'], predicted_amounts, 1)
        p = np.poly1d(z)
        ax_main.plot(df['original principal amount'], p(df['original principal amount']), "r--", alpha=0.8)

        ax_right.hist(predicted_amounts, bins=50, orientation='horizontal', alpha=0.5)
        ax_top.hist(df['original principal amount'], bins=50, alpha=0.5)

        ax_main.set_xlabel('Original Principal Amount')
        ax_main.set_ylabel('Predicted Disbursed Amount')
        ax_right.set_xlabel('Count')
        ax_top.set_ylabel('Count')

        plt.suptitle('Disbursed Amount vs. Original Principal Amount')
        plt.tight_layout()
        safe_plot_save(fig, 'disbursed_vs_principal.png', output_file_path)
        
        print("\nDisbursed Amount vs. Original Principal Amount Insight:")
        correlation = stats.pearsonr(df['original principal amount'], predicted_amounts)[0]
        print(f"Correlation between original principal and predicted disbursed amount: {correlation:.4f}")
        print("\nInsight: There is a strong relationship between the original principal amount and the predicted disbursed amount.")
        print("This insight helps in assessing fund utilization efficiency and project financial management.")
    except Exception as e:
        print(f"Error in disbursed amount prediction: {str(e)}")

