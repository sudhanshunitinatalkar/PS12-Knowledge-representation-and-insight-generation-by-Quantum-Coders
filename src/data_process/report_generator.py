import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

def generate_financial_analysis(raw_report, output_file_path):
    # Configure the API
    genai.configure(api_key=gemini_api_key)
    # Create the model
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 0,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    # Initialize the model
    model = genai.GenerativeModel(
        model_name="gemini-1.0-pro",
        generation_config=generation_config,
    )

    # Predefined prompt
    predefined_prompt = """You are a financial analyst specializing in loan portfolio analysis. Given raw data about loan distributions, statuses, interest rates, and disbursements, your task is to generate insightful analyses in a narrative, paragraph-based format. 

    For each major aspect of the data (e.g., Regional Distribution, Loan Status Distribution, Interest Rate Analysis, Disbursed Amount vs. Original Principal Amount), please:

    1. Create a paragraph of 4-6 sentences that flows naturally and tells a coherent story about the data.
    2. Begin with an overview of the key findings, then delve into specific details and numbers.
    3. Highlight important patterns, correlations, or outliers within the data.
    4. Explain the potential implications of these insights for loan management, risk assessment, and financial strategy.
    5. Use precise figures and percentages to support your analysis, integrating them smoothly into the narrative.
    6. Conclude each paragraph with a brief statement on how these insights could inform future decision-making or strategy.

    Maintain a professional yet accessible tone throughout your analysis. Focus on presenting a clear, comprehensive picture of each aspect of the loan portfolio data, emphasizing actionable insights that would be valuable to financial decision-makers.

    Here's the raw data for your analysis:

    Please begin your analysis, presenting each major aspect in a separate, well-structured paragraph.
    """

    # Combine predefined prompt and input text
    full_prompt = predefined_prompt + raw_report

    # Send the message and get the response
    try:
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(full_prompt)
    except Exception as e:
        print(f"Error: Failed to generate response from Gemini API. {str(e)}")
        return

    # Save the result to a text file
    try:
        with open(output_file_path, "w") as file:
            file.write(response.text)
        print(f"Response saved to {output_file_path}")
    except IOError:
        print(f"Error: Unable to write to output file '{output_file_path}'.")
