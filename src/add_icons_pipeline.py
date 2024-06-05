from pathlib import Path
from typing import Optional

from fuzzywuzzy import process
import fontawesome as fa
import pandas as pd
from tqdm import tqdm
from transformers import TFMarianMTModel, MarianTokenizer, TranslationPipeline

from data_processing_utilities import load_csv_as_df, export_df_as_csv
from logging_utils import get_logger

logger = get_logger(__name__)

def find_most_similar_icon(value: str) -> str:
    # Get all icons from fontawesome
    icons = fa.icons

    # Get the most similar icon to the value
    most_similar_icon = process.extractOne(value, icons.keys())

    return most_similar_icon[0]


def icon_search_by_column_pipeline(
    df: pd.DataFrame, column_to_search: str, column_to_add: str = "fa-icon"
) -> pd.DataFrame:
    logger.info(f"Starting icon search from column {column_to_search} pipeline...")
    tqdm.pandas()
    # Create a new pandas Series by applying the find_most_similar_icon function to the 'en_anlaegsbetydning' column
    icon_series = df[column_to_search].progress_apply(find_most_similar_icon)

    # Add this Series as a new column to the DataFrame, get the index of en_anlaegsbetydning, add 1 to it, so its just to the right
    df.insert(
        loc=df.columns.get_loc(column_to_search) + 1,
        column=column_to_add,
        value=icon_series,
    )

    logger.info(f"Added new column '{column_to_add}' to DataFrame")

    return df


def translate_dataframe_column_dk_to_en(
    df: pd.DataFrame,
    output_csv_path: Path,
    column_to_translate: str,
    translated_column_name: str = None,
    export_resulting_df: bool = False,
) -> pd.DataFrame:
    # Dynamically construct column name if not provided
    if not translated_column_name:
        translated_column_name = f"En_{column_to_translate}"

    # Instantiate model and tokenizer, hardcoded to use model for Danish to English translation
    model = TFMarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-da-en")
    tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-da-en")

    # Create a translation pipeline for Danish to English translation from model and tokenizer
    translator = TranslationPipeline(model=model, tokenizer=tokenizer, framework="tf")

    tqdm.pandas()

    logger.info(f"Starting translation of column {column_to_translate} from Danish to English...")
    # Create a new pandas Series by applying the translator to every value from the specified column
    english_translations = df[column_to_translate].progress_apply(
        lambda text: translator(text)[0]["translation_text"]
    )

    # Convert the encoding of the translated text from UTF-8 to ISO-8859-1 to match df encoding
    english_translations = english_translations.apply(lambda text: text.encode('utf-8').decode('ISO-8859-1', 'ignore'))

    # Add this Series as a new column to the DataFrame, get the index of the specified column, add 1 to it, so its just to the right
    df.insert(
        loc=df.columns.get_loc(column_to_translate) + 1,
        column=f"en_{column_to_translate}",
        value=english_translations,
    )

    if export_resulting_df:
        export_df_as_csv(df, output_csv_path.parent, output_csv_path.name)

    return df


def main():
    input_csv_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "output"
        / "anlaegsbetydning_value_counts.csv"
    )
    output_csv_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "output"
        / "anlaeg_all_25832_translated.csv"
    )

    df = load_csv_as_df(
        input_csv_path,
        csv_encoding="ISO-8859-1",
        columns_to_load=None,
        column_dtypes=None,
    )

    df = translate_dataframe_column_dk_to_en(
        df=df,
        output_csv_path=output_csv_path,
        column_to_translate="anlaegsbetydning",
    )

    df = icon_search_by_column_pipeline(df, "en_anlaegsbetydning")

    export_df_as_csv(df, output_csv_path.parent, output_csv_path.name, encoding="ISO-8859-1")


if __name__ == "__main__":
    main()
