import os
from pathlib import Path
from typing import List

import geopandas as gpd
import pandas as pd

from code_utilities import timing_decorator
from data_processing_utilities import load_csv_as_df, export_df_as_csv, get_file_size
from logging_utils import get_logger

logger = get_logger(__name__)

def filter_out_unnecessary_columns(input_path: Path, columns_to_remove: List[str], output_path: Path = None,) -> gpd.GeoDataFrame:
    # Handle default value for output_path when not provided..
    if output_path is None:
        output_path = input_path

    # Get the shapefile file size, just for clarity in the log message
    shapefile_file_size = get_file_size(input_path)

    logger.info(f"Attempting to load shapefile from {input_path} ({shapefile_file_size} mb). This may take some time for large files...")
    try:
        gdf = gpd.read_file(input_path)
    except Exception as e:
        logger.error(f"Error loading shapefile from {input_path}. {e}")
        raise
    logger.info("Shapefile loaded successfully!")
    
    logger.debug(f"GeoDataFrame head before removing columns: {gdf.head()}")

    for column in columns_to_remove:
        try:
            gdf = gdf.drop(columns=column)
        except KeyError:
            logger.error(f"Column {column} not found in GeoDataFrame. Skipping this column.")
    logger.debug(f"GeoDataFrame head after removing columns: {gdf.head()}")
    
    logger.info(f"Exporting filtered GeoDataFrame to {output_path}...")
    gdf.to_file(output_path, driver='ESRI Shapefile')

    return gdf


def main():
    input_csv_path = (
        Path(__file__).resolve().parents[1] / "data" / "input" / "anlaeg_all_25832.csv"
    )

    columns = ["anlaegsbetydning"]
    dtypes = {"anlaegsbetydning": str}

    # Load the CSV file as a DataFrame
    df = load_csv_as_df(
        input_csv_path,
        csv_encoding="ISO-8859-1",
        columns_to_load=None,
        column_dtypes=None,
    )

    # Calculate value counts
    value_counts = df.loc[:, "anlaegsbetydning"].value_counts()

    # Calculate the most common datering for each anlaegsbetydning
    most_common_datering = df.groupby("anlaegsbetydning")["datering"].agg(
        pd.Series.mode
    )
    most_common_datering_df = most_common_datering.reset_index()

    datering_distribution_per_group = df.groupby("anlaegsbetydning")[
        "datering"
    ].value_counts()

    # Convert the series into a DataFrame
    datering_distribution_per_group_df = datering_distribution_per_group.reset_index(
        name="count"
    )

    # Convert 'datering' and 'count' into a dictionary grouped by 'anlaegsbetydning'
    datering_distribution_dict = (
        datering_distribution_per_group_df.groupby("anlaegsbetydning")[[
            "datering", "count"
        ]]
        .apply(
            lambda x: (
                dict(zip(x["datering"], x["count"]))
                if "datering" in x.columns and "count" in x.columns
                else {}
            )
        )
        .reset_index(name="datering_distributions")
    )

    # Create a new DataFrame
    value_counts_df = value_counts.reset_index()

    # Merge value_counts_df and most_common_datering_df on 'anlaegsbetydning'
    value_counts_df = value_counts_df.merge(
        most_common_datering_df, on="anlaegsbetydning", how="left"
    )

    # Merge value_counts_df and datering_distribution_dict on 'anlaegsbetydning'
    value_counts_df = value_counts_df.merge(
        datering_distribution_dict, on="anlaegsbetydning", how="left"
    )

    # Rename the columns
    value_counts_df.columns = [
        "anlaegsbetydning",
        "counts",
        "most_frequent_datering",
        "datering_distributions",
    ]

    export_df_as_csv(
        value_counts_df,
        directory=Path(__file__).resolve().parents[1] / "data" / "output",
        filename="anlaegsbetydning_value_counts",
    )

    # Initialize input/output paths
    shapefile_path = Path(__file__).resolve().parents[1] / "data" / "input" / "anlaeg_all_25832.shp"
    cleaned_shapefile_output_path = Path(__file__).resolve().parents[1] / "data" / "output" / "cleaned_anlaeg_all_25832.shp"

    # Define columns to filter
    columns_to_delete = ["systemnr", "stednr", "loknr", "sbext", "frednr", "anlnr", "anlaegstyp", "dateringskode", "fra_aar", "til_aar", "kommunenavn", "kommunenr", "sevaerdighedsklasse"]

    gdf = filter_out_unnecessary_columns(shapefile_path, columns_to_delete, cleaned_shapefile_output_path) 

    logger.info("Script completed!")


if __name__ == "__main__":
    main()
