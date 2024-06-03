import os
from pathlib import Path

from dotenv import load_dotenv
from hugchat import hugchat
from hugchat.login import Login
import numpy as np
from tqdm import tqdm

from data_processing_utilities import load_csv_as_df, export_df_as_csv
from logging_utils import get_logger

logger = get_logger(__name__)

PROMPT = "Din opgave er at generere en general kort definition af en specifik type fortidsminde. Definitionen bør være 1-2 linjer. Definitionen skal bruges til en spændende app som skal engagere danskere i kulturarv. TYPE:"


def construct_hf_query(anlaegstype: str) -> str:
    return f"Din opgave er at generere en general kort definition af en specifik type fortidsminde. Definitionen bør være 1-2 linjer. Definitionen skal bruges til en spændende app som skal engagere danskere i kulturarv. TYPE: {anlaegstype}"


def process_anlagesbetydning(value):
    logger.info(f"Processing anlaegsbetydning: {value}...")
    definition = chatbot.query(construct_hf_query(value), web_search=True)
    logger.info(f"Definition for {value}: {definition}")
    return definition


# Load environment variables from .env file
env_file_path = Path(__file__).resolve().parents[1] / "data" / "hf_creds.env"
load_dotenv(dotenv_path=env_file_path)

# Load fortidsminder data, anlaegsbetydninger for descriptions
input_csv_path = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "output"
    / "anlaegsbetydning_value_counts.csv"
)
df = load_csv_as_df(input_csv_path)

# Get environment variables
EMAIL = os.getenv("EMAIL")
PASSWD = os.getenv("PASSWORD")

cookie_path_dir = "./cookies/"  # Note: trailing slash (/) is required to avoid errors
sign = Login(EMAIL, PASSWD)
cookies = sign.login(cookie_dir_path=cookie_path_dir, save_cookies=True)

# Create a chatbot instance
chatbot = hugchat.ChatBot(
    cookies=cookies.get_dict()
)  # or cookie_path="usercookies/<email>.json"

print(f"Created chatbot instance using the following model: {chatbot.active_model}")

# Initialize an empty list to store the definitions
definitions = []

# Iterate over the first 10 rows of the 'anlaegsbetydning' column
for value in df['anlaegsbetydning'].iloc[:10]:
    # Process the value and append the result to the definitions list
    definitions.append(process_anlagesbetydning(value))

# Fill the rest of the 'definition' column with np.nan
definitions += [np.nan] * (len(df) - 10)

# Add the definitions list as a new column to the DataFrame
df['definition'] = definitions

output_path = Path(__file__).resolve().parents[1] / "data" / "output"
export_df_as_csv(df, output_path, "anlaegsbetydning_with_definitions.csv")
