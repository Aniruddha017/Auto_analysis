import os
import sys
import pandas as pd
import seaborn as sns
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import httpx
import chardet
from typing import Dict, Any

class Autolysis:
    def __init__(self, file_path: str, api_url: str, api_token: str):
        """Initialize the Autolysis class with necessary parameters."""
        self.file_path = file_path
        self.api_url = api_url
        self.api_token = api_token
        self.data_frame = None

    def load_csv_data(self) -> pd.DataFrame:
        """Load CSV data with encoding detection."""
        if not os.path.isfile(self.file_path):
            print(f"Error: File '{self.file_path}' not found.")
            sys.exit(1)
        with open(self.file_path, 'rb') as file_handle:
            encoding_result = chardet.detect(file_handle.read())
        detected_encoding = encoding_result['encoding']
        print(f"Detected file encoding: {detected_encoding}")
        self.data_frame = pd.read_csv(self.file_path, encoding=detected_encoding)
        return self.data_frame

    def perform_data_analysis(self) -> Dict[str, Any]:
        """Perform basic data analysis."""
        if self.data_frame is None or self.data_frame.empty:
            print("Error: Dataset is empty.")
            sys.exit(1)
        numeric_data_frame = self.data_frame.select_dtypes(include=['number'])  # Select only numeric columns
        analysis_results = {
            'summary': self.data_frame.describe(include='all').to_dict(),
            'missing_values': self.data_frame.isnull().sum().to_dict(),
            'correlation': numeric_data_frame.corr().to_dict()  # Compute correlation only on numeric columns
        }
        print("Data analysis complete.")
        return analysis_results

    def create_visualizations(self):
        """Generate and save visualizations."""
        sns.set(style="whitegrid")
        numeric_columns = self.data_frame.select_dtypes(include=['number']).columns
        if numeric_columns.empty:
            print("No numeric columns found for visualization.")
            return
        for numeric_column in numeric_columns:
            plt.figure()
            sns.histplot(self.data_frame[numeric_column].dropna(), kde=True)
            plt.title(f'Distribution of {numeric_column}')
            file_name = f'{numeric_column}_distribution.png'
            plt.savefig(file_name)
            print(f"Saved distribution plot: {file_name}")
            plt.close()

    def generate_analysis_narrative(self, analysis_data: Dict[str, Any]) -> str:
        """Generate narrative using LLM."""
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        prompt_message = f"Provide a detailed analysis based on the following data summary: {analysis_data}"
        request_data = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": prompt_message}]
        }
        try:
            response = httpx.post(self.api_url, headers=headers, json=request_data, timeout=30.0)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except httpx.HTTPStatusError as http_error:
            print(f"HTTP error occurred: {http_error}")
        except httpx.RequestError as request_error:
            print(f"Request error occurred: {request_error}")
        except Exception as general_error:
            print(f"An unexpected error occurred: {general_error}")
        return "Narrative generation failed due to an error."

    def process(self):
        """Execute the full autolysis process."""
        print("Starting autolysis process...")
        self.load_csv_data()
        print("Dataset loaded successfully.")
        
        print("Analyzing data...")
        analysis_data = self.perform_data_analysis()
        
        print("Generating visualizations...")
        self.create_visualizations()
        
        print("Generating narrative...")
        narrative_output = self.generate_analysis_narrative(analysis_data)
        
        if narrative_output != "Narrative generation failed due to an error.":
            with open('README.md', 'w') as readme_file:
                readme_file.write(narrative_output)
            print("Narrative successfully written to README.md.")
        else:
            print("Narrative generation failed. Skipping README creation.")
        
        print("Autolysis process completed.")


def main():
    """Main entry point for the program."""
    if len(sys.argv) != 2:
        print("Usage: python autolysis.py <file_path>")
        sys.exit(1)
    
    # Fetch API token from environment variable
    api_token = os.getenv("AIPROXY_TOKEN")
    if not api_token:
        print("Error: API token not set in environment variables.")
        sys.exit(1)
    
    # Instantiate the Autolysis class and start the process
    autolysis = Autolysis(file_path=sys.argv[1], api_url="https://aiproxy.sanand.workers.dev/openai/v1/chat/completions", api_token=api_token)
    autolysis.process()


if __name__ == "__main__":
    main()