from pathlib import Path
from typing import Dict, List, Optional, Union

import chardet
import numpy as np
import pandas as pd

from code_utilities import timing_decorator
from logging_utils import get_logger

logger = get_logger(__name__)


@timing_decorator(logger=logger)
def load_csv_as_df(
    file_path: Path,
    columns_to_load: Optional[List[str]] = None,
    column_dtypes: Optional[Dict[str, Union[str, type]]] = None,
    csv_encoding: Optional[str] = None,
) -> pd.DataFrame:
    logger.info(f"Attempting to load csv from {file_path}...")

    if csv_encoding is None:
        logger.info("Attempting to detect file encoding...")

        # Attempt to detect the file encoding with chardet library
        with open(file_path, "rb") as f:
            result = chardet.detect(f.read())
            csv_encoding = result["encoding"]
            logger.info(f"Detected encoding: {csv_encoding}")

    logger.info(f"Attempting to load csv file with encoding {csv_encoding}...")
    try:
        df = pd.read_csv(
            file_path,
            encoding=csv_encoding,
            usecols=columns_to_load,
            dtype=column_dtypes,
            engine="c",
        )
    except Exception as e:
        logger.error(
            f"Error loading file with detected encoding {result['encoding']}: {e}"
        )
        raise

    return df


def export_df_as_csv(df: pd.DataFrame, directory: Path, filename: str) -> None:
    """
    Export a pandas DataFrame as a CSV file.

    Parameters:
        df (pd.DataFrame): The DataFrame to be exported.
        directory (Path): The directory where the CSV file will be saved.
        filename (str): The name of the CSV file.

    Raises:
        PermissionError: If the function does not have permission to create the directory or write the file.
        OSError: If an OS error occurs when trying to create the directory.
        Exception: If an unexpected error occurs when trying to write to the file.
    """
    try:
        # Create the directory if it doesn't exist
        directory.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        logger.error(f"Permission denied when trying to create directory: {directory}")
        return
    except OSError as e:
        logger.error(f"OS error occurred when trying to create directory: {e}")
        return

    # Check if filename ends with .csv, if not, append it
    if not filename.endswith(".csv"):
        filename += ".csv"

    # Create the full file path
    file_path = directory / filename

    logger.info(f"Trying to export DataFrame to CSV: {file_path}")
    try:
        df.to_csv(file_path, index=False)
        logger.info(f"Successfully exported DataFrame to CSV: {file_path}")
    except PermissionError:
        logger.error(f"Permission denied when trying to write to file: {file_path}")
    except Exception as e:
        logger.error(f"Unexpected error occurred when trying to write to file: {e}")

def add_empty_columns_to_df(
    df: pd.DataFrame, columns: List[str], dtypes: Dict[str, str] = None
) -> pd.DataFrame:
    for column in columns:
        if column not in df.columns:
            df = df.assign(**{column: np.nan})
            if dtypes and column in dtypes:
                df[column] = df[column].astype(dtypes[column])
    return df