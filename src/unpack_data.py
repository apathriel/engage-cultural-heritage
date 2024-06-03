import argparse
from pathlib import Path
import zipfile

from logging_utils import get_logger

# Setup logger 
logger = get_logger(__name__)


def extract_zip(zip_path, extract_path):
    logger.info(f"Extracting zip {zip_path.stem} to {extract_path}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
    logger.info(f"Extraction complete")


def get_cli_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--zip_file_name",
        "-z",
        type=str,
        help="Filename of the zip file to extract. Must be located in the 'im' directory",
        default="sevanlaeg_all_4326_shp.zip",
        required=True,
    )
    parser.add_argument(
        "--extract_path",
        "-e",
        type=str,
        help="Path to extract the zip file contents to",
        default=None,
        required=False,
    )
    parser.add_argument(
        "--delete_zip",
        "-d",
        action="store_true",
        help="Flag determining if the zip file should be deletedafter extraction",
        default=False,
    )

    args = parser.parse_args()

    # Add .zip extension to --zip_path if not present
    if not args.zip_file_name.endswith(".zip"):
        args.zip_path += ".zip"

    return args


def main():
    # Get CLI arguments
    args = get_cli_args()

    # Define paths to input directory + zip file
    input_directory = Path(__file__).resolve().parents[1] / "data"
    zip_file_name = args.zip_file_name
    zip_path = input_directory / zip_file_name

    # Define path to extract the zip file to, defaults to input directory
    extract_path = Path(args.extract_path) if args.extract_path else input_directory

    # Extract zip file
    extract_zip(zip_path, extract_path)

    # Remove the zip file after extraction
    if args.delete_zip:
        logger.info(f"Attempting to delete... {zip_path}")
        zip_path.unlink()
        logger.info(f"Sucessfully deleted {zip_path}!")


if __name__ == "__main__":
    main()
