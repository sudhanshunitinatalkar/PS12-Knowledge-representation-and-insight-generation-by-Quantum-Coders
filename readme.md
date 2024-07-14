# PS-12: Knowledge Representation and Insights Generation from Structured Datasets


We are Quantum Coders, Team Leader **Krushna Mohod** and Team Member **Sudhanshu Atalkar** from **Prof. Ram Meghe Institute of Technology and Research**

## Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Installation](#installation)
   - [Prerequisites](#prerequisites)
   - [Setup Instructions](#setup-instructions)
4. [Usage](#usage)
5. [Project Structure](#project-structure)
6. [Acknowledgements](#acknowledgements)

## Additional Resources

Due to size limitations on GitHub, some larger project files are stored separately. These include:

- **models folder**: Contains trained machine learning models
- **data folder**: Contains the dataset used for this project

These resources can be found in our Google Drive folder.

To use these resources:

1. Download the 'models.zip' and 'data.zip' files from the provided Google Drive link:
   [https://drive.google.com/drive/folders/1xLQ_kKhFmsJlCY1j2-Fdlm-G98-yEgSL?usp=sharing](https://drive.google.com/drive/folders/1xLQ_kKhFmsJlCY1j2-Fdlm-G98-yEgSL?usp=sharing)

2. Extract both zip files in the root directory of the project, alongside the other folders and files. This will create 'models' and 'data' folders.

3. Ensure that the extracted 'models' and 'data' folders are placed directly in the root directory of the project.

This will ensure that all scripts and applications can access the necessary data and models.


## Project Overview

This project aims to provide comprehensive insights from the IBRD loans and credits dataset through a user-friendly web application. The application leverages both CPU and GPU processing to efficiently handle large datasets and perform complex analyses. This Project has two parts one which runs solely on the cpu for device compatility across all devices which utilises parallel processing for scalability and the other part runs the preprocessing on the cuda suppoerted GPU's using RAPIDS libraries for gpu accelerated computing. After uploading dataset, preprocessing is performed. Knowledge of dataset is represented in form of visualizations. Insights are generated after identifying pattern with integration of Gemini 1.5 Pro LLM.
Source of the dataset: https://finances.worldbank.org/Loans-and-Credits/IBRD-Statement-Of-Loans-Historical-Data/zucq-nrc3/about_data

## Features

- Data cleaning and preprocessing
- GPU acceleration with RAPIDS for data processing
- Parallel processing using `concurrent.futures`
- Interactive visualizations
- Insights generation using machine learning models
- Web interface built with Flask



## Installation

### System Requirements for CPU

- RAM: Minimum 16 GB
- Processor: Intel i5/i7 or AMD Ryzen 5/7 (or equivalent)
- Operating System: Windows or Linux
- Disk Space: Minimum 7GB

### System Requirements for GPU

- RAM: Minimum 16 GB
- Processor: Intel i5/i7 or AMD Ryzen 5/7 (or equivalent)
- Operating System: Linux only (WSL not supported)
- Disk Space: Minimum 7GB
- GPU: NVIDIA GPU with CUDA support (version 11.8 or above)
- VRAM: Minimum 4GB


### Setup Instructions For GPU

1. **Clone the repository:**

    ```
    git clone https://github.com/sudhanshunitinatalkar/PS12-Knowledge-representation-and-insight-generation-by-Quantum-Coders.git
    cd PS12-Knowledge-representation-and-insight-generation-by-Quantum-Coders
    ```

2. **Set up RAPIDS environment:**`

    Follow the instructions for installing RAPIDS on your system: [RAPIDS Installation Guide](https://rapids.ai/start.html#get-rapids)


3. **Install the required packages:**

    ```
    pip install -r requirements.txt
    ```

4. **Set up Gemini api key:**
   
   In the root directory of the project there is a file named .env, append your gemini api key  "GEMINI_API_KEY=" here.


5. **Run the application:(In the root directory of the project)**

    ```
    python GPU_app.py
    ```

### Setup Instructions For CPU

1. **Clone the repository:**

    ```
    git clone https://github.com/sudhanshunitinatalkar/PS12-Knowledge-representation-and-insight-generation-by-Quantum-Coders.git
    cd PS12-Knowledge-representation-and-insight-generation-by-Quantum-Coders
    ```

2. **Install the required packages:**

    ```
    pip install -r requirements.txt
    ```

3. **Set up Gemini api key:**
   
   In the root directory of the project there is a file named .env, append your gemini api key  "GEMINI_API_KEY=" here.


4. **Run the application:(In the root directory of the project)**

    ```
    python CPU_app.py
  

## Usage

1. **Access the web application:**

    Make sure you are connected to the internet. After running the application, open your web browser and navigate to the URL starting with 192.168....

2. **Upload your dataset:**

    Use the web interface to upload the IBRD loans and credits dataset. Sample datasets can be found in the `Dataset` folder.

3. **Generate insights:**

    Explore various insights and visualizations generated by the application. Navigate through different sections of the web interface to view data insights and visualizations.

## Project Structure

```
.
├── CPU_app.py
├── GPU_app.py
├── data
│   └── IBRD_Statement_Of_Loans_-_Historical_Data_20240713.csv
├── models
│   ├── disbursed_amount_rf_model.joblib
│   ├── encoder_decoder.joblib
│   ├── interest_rate_rf_model.joblib
│   └── loan_status_rf_model.joblib
├── notebooks
│   └── preprocessing_eda.ipynb
├── readme.md
├── reports
│   ├── PS12-knowldge-representation-and-insight-generation-from-structured-dataset-project-presentation.pptx
│   ├── PS12-knowldge-representation-and-insight-generation-from-structured-dataset-project-report.pdf
│   └── Team-Contribution-Report.pdf
├── requirements.txt
├── scripts
│   └── model_training.py
└── src
    ├── data_process
    │   ├── chatbox.py
    │   ├── CPU_columnclassifier.py
    │   ├── CPU_data_preprocessor_for_insights.py
    │   ├── CPU_data_preprocessor_for_visualisation.py
    │   ├── CPU_insight_generator_complete.py
    │   ├── GPU_columnclassifier.py
    │   ├── GPU_data_preprocessor_for_insights.py
    │   ├── GPU_data_preprocessor_for_visualisation.py
    │   ├── GPU_insight_generator_complete.py
    │   ├── raw_insight_maker.py
    │   ├── report_generator.py
    │   └── visuals_generator.py
    ├── insights_processed
    ├── insights_upload
    ├── static
    │   ├── css
    │   │   └── styles.css
    │   ├── images
    │   │   ├── arpitsir.jpg
    │   │   ├── favicon.ico
    │   │   ├── karwasir.jpg
    │   │   ├── krushna.jpg
    │   │   ├── sudhanshu.jpg
    │   │   └── yogitamadam.jpg
    │   └── js
    │       ├── insights.js
    │       ├── script.js
    │       └── visualize.js
    ├── templates
    │   ├── about.html
    │   ├── contact.html
    │   ├── explore.html
    │   ├── home.html
    │   ├── index.html
    │   ├── insights.html
    │   └── visualize.html
    ├── visuals_processed
    └── visuals_upload



## Acknowledgements

We would like to thank the Intel Unnati program for providing this opportunity and resources. Special thanks to the RAPIDS team for their GPU-accelerated data processing libraries.
