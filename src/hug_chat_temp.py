import os
from pathlib import Path
from typing import List, Optional, Tuple, Union

from dotenv import load_dotenv
from hugchat import hugchat
from hugchat.login import Login
import numpy as np
import pandas as pd
from tqdm import tqdm

from code_utilities import timing_decorator
from data_processing_utilities import load_csv_as_df, export_df_as_csv
from logging_utils import get_logger

logger = get_logger(__name__)
logger.propagate = False

PROMPT = "Din opgave er at generere en general kort definition af en specifik type fortidsminde. Definitionen bør være 1-2 linjer. Definitionen skal bruges til en spændende app som skal engagere danskere i kulturarv. TYPE:"


def combine_chunk_files(
    chunk_file_prefix: str = "chunk_", output_file: str = "combined.csv"
) -> pd.DataFrame:
    # Get a list of all chunk files
    chunk_files = list(Path(".").glob(f"{chunk_file_prefix}*.csv"))

    # Sort the files by chunk id
    chunk_files.sort(key=lambda x: int(x.stem[len(chunk_file_prefix) :]))

    # Combine all chunk files into a single DataFrame
    combined_df = pd.concat((pd.read_csv(file) for file in chunk_files))

    # Save the combined DataFrame to a file
    combined_df.to_csv(output_file, index=False)

    return combined_df


def process_chunk_from_df(chunk, chatbot):
    results = []
    for value in tqdm(chunk["anlaegsbetydning"], desc="Processing values"):
        try:
            result = generate_anlaegsbetydning_pipeline(value, chatbot)
        except Exception as e:
            logger.info(f"Failed to process value {value}: {e}")
            result = (np.nan, np.nan)
        results.append(result)
    return results


def construct_hf_query(anlaegstype: str) -> str:
    return f"Din opgave er at generere en general kort definition af en specifik type fortidsminde. Definitionen bør være 1-2 linjer. Definitionen skal bruges til en spændende app som skal engagere danskere i kulturarv. TYPE: {anlaegstype}"


def prompt_hf_chatbot(
    chatbot: hugchat.ChatBot, prompt: str, use_web_search: bool = True
) -> hugchat.Message:
    logger.debug(f"Prompting chatbot with the following message: {prompt}...")
    message = chatbot.chat(prompt, web_search=use_web_search)
    logger.debug("Message sent to chatbot.")
    message.wait_until_done()
    logger.debug("Chatbot processing completed.")
    return message


def generate_anlaegsbetydning_pipeline(
    value: str, chatbot_instance: hugchat.ChatBot, use_web_search: bool = True
) -> Union[str, Tuple[str, List[str]]]:
    """
    This function generates a pipeline for anlaegsbetydning.

    Parameters:
    value (str): The value to process.
    use_web_search (bool): Flag to indicate whether to use web search or not. Default is True.

    Returns:
    Union[str, Tuple[str, List[str]]]: Returns the definition and optionally the sources if web search is enabled.
    """
    logger.info(f"Attempting to process anlaegsbetydning: {value}...")
    try:
        message = prompt_hf_chatbot(
            chatbot=chatbot_instance,
            prompt=construct_hf_query(value),
            use_web_search=use_web_search,
        )

        definition = message.get_final_text()
        logger.info(f"Final text from chatbot: {definition}")

        if message.search_enabled():
            try:
                sources = [source.link for source in message.get_search_sources()]
                logger.info(
                    f"Successfully generated RAG definition for anlaegstype {value}. Returning definition and sources..."
                )
                return definition, sources
            except Exception as e:
                logger.error(
                    f"An error occurred while getting search sources: {e}. Returning definition and empty list..."
                )
                return definition, []

        logger.info(f"Successfully generated definition for anlaegstype {value}")
        return definition
    except Exception as e:
        logger.error(
            f"An error occurred while generating anlaegsbetydning pipeline: {e}"
        )
        if use_web_search:
            return f"ERROR {e}: COULD NOT GENERATE DEFINITION", []
        else:
            return f"ERROR {e}: COULD NOT GENERATE DEFINITION"


@timing_decorator(logger=logger)
def generate_definitions_from_dataframe(
    df: pd.DataFrame,
    chatbot: hugchat.ChatBot,
    chunk_size: int = 8,
    use_chunks: bool = True,
    chunk_dir: Optional[Path] = None,
    num_rows: Optional[int] = None,
) -> pd.DataFrame:
    if chunk_dir is None:
        chunk_dir = Path(__file__).resolve().parents[0]
        
    if use_chunks:
        # Create chunk indices
        chunk_indices = np.arange(len(df)) // chunk_size

        for chunk_id, chunk in tqdm(
            df.groupby(chunk_indices), desc="Processing chunks"
        ):
            logger.info(f"Processing chunk {chunk_id}...")
            generation_results = process_chunk_from_df(chunk, chatbot)

            # Unpack the results into two lists
            definitions, web_search_sources = map(list, zip(*generation_results))

            # Add the lists as new columns to the chunk
            chunk["definition"] = definitions
            chunk["web_search_sources"] = web_search_sources

            # Save the chunk to a file
            chunk.to_csv(chunk_dir / f"chunk_{chunk_id}.csv")
    else:
        if num_rows is None:
            num_rows = len(df)

        logger.info(f"Processing the first {num_rows} rows of the DataFrame...")
        
        generated_results = []

        for value in tqdm(df['anlaegsbetydning'].iloc[:num_rows]):
            try:
                generation = generate_anlaegsbetydning_pipeline(value, chatbot)
            except Exception as e:
                logger.info(f"Failed to process value {value}: {e}")
                generation = (np.nan, np.nan)

            generated_results.append(generation)

        # Add np.nan for the remaining rows
        generated_results += [(np.nan, np.nan)] * (len(df) - num_rows)

        # Unpack the results into two lists
        definitions, web_search_sources = map(list, zip(*generated_results))

        # Add the lists as new columns to the DataFrame
        df["definition"] = definitions
        df["web_search_sources"] = web_search_sources

    return df


def main():
    # Load environment variables from .env file
    env_file_path = Path(__file__).resolve().parents[1] / "data" / "hf_creds.env"
    load_dotenv(dotenv_path=env_file_path)

    # Get environment variables for HF sign in
    EMAIL = os.getenv("EMAIL")
    PASSWD = os.getenv("PASSWORD")

    # Load fortidsminder data, anlaegsbetydninger for descriptions
    input_csv_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "output"
        / "anlaegsbetydning_value_counts.csv"
    )

    chunk_output_dir = Path(__file__).resolve().parents[1] / "data" / "output" / "temp"
    chunk_output_dir.mkdir(parents=True, exist_ok=True)

    df = load_csv_as_df(input_csv_path)

    cookie_path_dir = (
        "./cookies/"  # Note: trailing slash (/) is required to avoid errors
    )
    sign = Login(EMAIL, PASSWD)
    cookies = sign.login(cookie_dir_path=cookie_path_dir, save_cookies=True)

    # Create a chatbot instance
    chatbot = hugchat.ChatBot(
        cookies=cookies.get_dict()
    )  # or cookie_path="usercookies/<email>.json"

    logger.info(
        f"Created chatbot instance using the following model: {chatbot.active_model}"
    )

    # Process the first 3 rows of the DataFrame
    processed_df = generate_definitions_from_dataframe(df, chatbot, use_chunks=False, num_rows=5)

    output_path = Path(__file__).resolve().parents[1] / "data" / "output"
    export_df_as_csv(processed_df, output_path, "anlaegsbetydning_with_definitions.csv")


if __name__ == "__main__":
    main()
