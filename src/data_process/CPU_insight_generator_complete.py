from src.data_process.CPU_data_preprocessor_for_insights import preprocess_insights
from src.data_process.raw_insight_maker import generate_insights
from src.data_process.report_generator import generate_financial_analysis

def aio_insights(input_path, output_path):
    # Step 1: Preprocess the data
    print("Starting data preprocessing...")
    df = preprocess_insights(input_path)
    print("Preprocessing completed. DataFrame shape:", df.shape)

    # Step 2: Generate insights
    print('output path', output_path)
    print("Generating insights...")                         
    raw_report = generate_insights(df, output_path)
    generate_financial_analysis(raw_report, 'src/insights_processed/generated_report.txt')
    print("Insights generation completed.")
    
    # delete df to save memory
    del df

