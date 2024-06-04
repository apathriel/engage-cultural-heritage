from pathlib import Path

import pandas as pd

from data_processing_utilities import load_csv_as_df, export_df_as_csv
from logging_utils import get_logger


logger = get_logger(__name__)


def main():
    input_csv_path = (
        Path(__file__).resolve().parents[1] / "data" / "anlaeg_all_25832.csv"
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

    logger.info("Script completed!")


if __name__ == "__main__":
    main()
