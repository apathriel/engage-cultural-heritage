from pathlib import Path
from typing import Optional

from fuzzywuzzy import process
import fontawesome as fa
import pandas as pd
from tqdm import tqdm
from transformers import TFMarianMTModel, MarianTokenizer, TranslationPipeline

from data_processing_utilities import load_csv_as_df, export_df_as_csv

def find_most_similar_icon(value: str) -> str:
    # Get all icons from fontawesome
    icons = fa.icons

    # Get the most similar icon to the value
    most_similar_icon = process.extractOne(value, icons)

    return most_similar_icon

def translate_dataframe_column_dk_to_en(
    input_csv_path: Path,
    output_csv_path: Path,
    column_to_translate: str,
    translated_column_name: str = None,
    export_resulting_df: bool = True,
    csv_encoding: Optional[str] = "ISO-8859-1",
) -> pd.DataFrame:
    # Dynamically construct column name if not provided
    if not translated_column_name:
        translated_column_name = f"en_{column_to_translate}"

    # Instantiate model and tokenizer, hardcoded to use model for Danish to English translation
    model = TFMarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-da-en")
    tokenizer = MarianTokenizer.from_pretrained("Helsinki-NLP/opus-mt-da-en")

    # Create a translation pipeline for Danish to English translation from model and tokenizer
    translator = TranslationPipeline(model=model, tokenizer=tokenizer, framework="tf")

    df = load_csv_as_df(
        input_csv_path,
        csv_encoding=csv_encoding,
        columns_to_load=None,
        column_dtypes=None,
    )

    tqdm.pandas()

    # Create a new pandas Series by applying the translator to every value from the specified column
    english_translations = df[column_to_translate].progress_apply(
        lambda text: translator(text)[0]["translation_text"]
    )

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

    df = translate_dataframe_column_dk_to_en(
        input_csv_path=input_csv_path,
        output_csv_path=output_csv_path,
        column_to_translate="anlaegsbetydning",
    )

    font_input = Path(__file__).resolve().parents[1] / "data" / "output" / ""
    

if __name__ == "__main__":
    main()