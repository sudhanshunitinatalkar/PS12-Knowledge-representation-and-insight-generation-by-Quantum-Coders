import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report, r2_score
from joblib import dump, load
import logging
import warnings
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

# Suppress warnings
warnings.filterwarnings('ignore')

# Create insight_model37 folder
os.makedirs('insight_model37', exist_ok=True)

# Define target variables
target_variables = {
    'regression': ['loan duration (days)', 'interest rate', 'disbursed amount'],
    'classification': ['loan status']
}

# Define features to exclude from predictors
exclude_features = ['loan number', 'end of period', 'project id', 'project name']

class EncoderDecoderModel:
    def __init__(self):
        self.encoders = {}

    def fit(self, df, columns):
        for column in columns:
            if df[column].dtype == 'object':
                le = LabelEncoder()
                le.fit(df[column])
                self.encoders[column] = le

    def encode(self, df, column):
        if column in self.encoders:
            return self.encoders[column].transform(df[column])
        return df[column]

    def decode(self, df, column):
        if column in self.encoders:
            return self.encoders[column].inverse_transform(df[column])
        return df[column]

def encode_categorical(df, column, encoder_decoder):
    if df[column].nunique() > 20:
        df[column] = encoder_decoder.encode(df, column)
    else:
        df = pd.get_dummies(df, columns=[column], prefix=column)
    return df

def train_rf(X, y, model_type='regression'):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    if model_type == 'regression':
        model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        return model, (mse, r2)
    else:
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)
        return model, (accuracy, report)

def process_target(df, target, task, encoder_decoder):
    logger.info(f"Processing target: {target}")
    
    X = df.drop(columns=exclude_features + list(target_variables['regression']) + list(target_variables['classification']))
    y = df[target].values
    
    for column in X.select_dtypes(include=['object']):
        X = encode_categorical(X, column, encoder_decoder)
    
    if task == 'classification':
        y = encoder_decoder.encode(df, target)
    
    model, metrics = train_rf(X, y, task)
    
    dump(model, f'insight_model37/{target}_rf_model.joblib')
    
    return model, metrics, X.columns.tolist()

def main():
    logger.info("Loading data...")
    df = pd.read_csv('IBRD_data_output.csv')
    
    logger.info("Initializing encoder-decoder...")
    encoder_decoder = EncoderDecoderModel()
    encoder_decoder.fit(df, df.columns)
    
    logger.info("Starting processing...")
    results = []
    
    for task, targets in target_variables.items():
        for target in targets:
            result = process_target(df, target, task, encoder_decoder)
            results.append((target, task, result))
    
    # Save encoder-decoder model
    dump(encoder_decoder, 'insight_model37/encoder_decoder.joblib')
    
    # Summarize results and save to file
    with open('insight_model37/model_performance.txt', 'w') as f:
        for target, task, (model, metrics, features) in results:
            summary = f"Target: {target}\n"
            summary += f"Task: {task}\n"
            if task == 'regression':
                mse, r2 = metrics
                summary += f"Random Forest MSE: {mse}\n"
                summary += f"Random Forest R2 Score: {r2}\n"
            else:
                accuracy, report = metrics
                summary += f"Random Forest Accuracy: {accuracy}\n"
                summary += f"Random Forest Classification Report:\n{report}\n"
            
            summary += f"Number of features used: {len(features)}\n"
            summary += "Top 10 important features:\n"
            feature_importances = pd.Series(model.feature_importances_, index=features).nlargest(10)
            for feature, importance in feature_importances.items():
                summary += f"  {feature}: {importance}\n"
            summary += "-" * 50 + "\n"
            
            f.write(summary)
            logger.info(summary)

    logger.info("Process completed. Results saved in 'insight_model37' folder.")

if __name__ == "__main__":
    main()