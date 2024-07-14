
import google.generativeai as genai
from dotenv import load_dotenv
import os
load_dotenv()

# Load your API key from an environment variable 
gemini_api_key = os.getenv("GEMINI_API_KEY")

# define the chatbox function with taking a query from the user
def chatbox(inputtext):

    # Configure the API
    genai.configure(api_key=gemini_api_key)

    # Configure the generation model
    generation_config = {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 0,
        "max_output_tokens": 4096,
        "response_mime_type": "text/plain",
    }

    # Create the model
    model = genai.GenerativeModel(
        model_name="gemini-1.0-pro",
        generation_config=generation_config,
    )

    # Predefined prompt
    predefined_prompt = """

You are an AI assistant with expertise in financial analysis, specifically loan portfolio management. You have been provided with a detailed analysis of a loan portfolio, covering four key aspects: Regional Distribution, Loan Status Distribution, Interest Rate Analysis, and Disbursed Amount vs. Original Principal Amount. Each aspect is summarized in a comprehensive paragraph.

Your task is to answer questions about this loan portfolio analysis in a clear, concise, and informative manner. When responding:

1. Draw information directly from the provided paragraphs.
2. Provide specific data points and percentages when relevant.
3. Offer brief explanations of financial concepts if necessary.
4. Highlight key insights and their potential implications for loan management and strategy.
5. Keep your answers focused and to the point, typically 2-4 sentences long unless more detail is explicitly requested.
6. If a question cannot be fully answered based on the given information, state this clearly and provide the best possible answer with the available data.

Remember, you are to act as if you have a deep understanding of this specific loan portfolio based solely on the four paragraphs of analysis provided. Do not introduce information that isn't present in the original analysis.

Please answer the following questions about the loan portfolio analysis:

    """

    # Path to the generated report
    file_path = 'src/insights_processed/generated_report.txt'

    # Read the generated report
    with open(file_path, 'r') as file:
        insights = file.read()

    query = inputtext

    # Generate the response
    full_prompt = insights + predefined_prompt + query


    try:
        # Start a new chat session with the AI model
        chat_session = model.start_chat(history=[])
        
        # Send the full prompt to the model and get the response
        response = chat_session.send_message(full_prompt)

        # Extract the text from the response
        response_text = response.text

    except Exception as e:

        # If an error occurs, print an error message and return None
        print(f"Error: Failed to generate response from Gemini API. {str(e)}")
        return None

    # Return the response text
    return response_text
