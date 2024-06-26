import argparse
import mimetypes
from pathlib import Path
import re
import requests
from urllib.parse import unquote
import zipfile

from logging_utils import get_logger

logger = get_logger(__name__)


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Download and optionally extract zip file from provided URL."
    )
    parser.add_argument(
        "--url",
        "-u",
        type=str,
        help="URL to download zip file from",
        default="https://sciencedata.dk/shared/ce0f8e62af16dab66b45f13be90d00f8?download",
        required=False,
    )
    parser.add_argument(
        "--download_target_dir",
        "-d",
        type=str,
        help="Directory to download the zip file to",
        default=None,
        required=False,
    )
    parser.add_argument(
        "--file_name",
        "-f",
        type=str,
        help="Optionally define the name of the downloaded file",
        default=None,
        required=False,
    )
    parser.add_argument(
        "--stream_downloads",
        "-s",
        action="store_true",
        help="Flag determining whether to stream downloads",
        default=False,
    )
    parser.add_argument(
        "--extract-zip", 
        "-ez", 
        action="store_true", 
        help="Extract the downloaded file.",
        default=True
    )
    parser.add_argument(
        "--delete-zip",
        "-dz",
        action="store_true",
        help="Delete the downloaded file after successful extraction.",
        default=True,    
    )
    return parser.parse_args()


class FileDownloader:
    def __init__(
        self,
        url: str,
        download_target_dir: Path,
        file_name: str = None,
        stream_downloads: bool = False,
    ):
        self.url = url
        self.download_target_dir = download_target_dir
        self.file_name = file_name
        self.stream_downloads = stream_downloads
        self.downloaded_file_path = None

    def update_download_file_path(self, file_path: Path) -> None:
        self.downloaded_file_path = file_path

    def download_file_from_url(self) -> None:
        logger.info(f"Attempting to download file from: {self.url}")
        try:
            logger.info("Sending GET request...")
            response = requests.get(self.url, stream=self.stream_downloads)
            response.raise_for_status()

            if self.file_name is None:
                logger.info(
                    "No file name provided. Determining file name from response headers..."
                )
                content_disposition = response.headers.get("Content-Disposition")

                # Trying to get the filename from Content-Disposition header, if fail try to infer from Content-Type with mimetypes
                if content_disposition:
                    file_name = re.findall('filename="(.+)"', content_disposition)
                    if file_name:
                        file_name = unquote(file_name[0])
                        logger.info(
                            f"File name [{file_name}] sucessfully extracted from Content-Disposition header!"
                        )

                if file_name is None:
                    content_type = response.headers["Content-Type"]
                    extension = mimetypes.guess_extension(content_type)
                    file_name = f"data{extension}"
                    logger.info(
                        f"File name [{file_name}] sucessfully inferred from Content-Type header!"
                    )
            else:
                file_name = self.file_name

            full_file_path = self.download_target_dir / file_name
            full_file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_file_path, "wb") as file:
                logger.info(f"Writing file to: {full_file_path}...")
                if self.stream_downloads:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:  # filter out the keep-alive new chunks
                            file.write(chunk)
                else:
                    file.write(response.content)

            logger.info(f"File downloaded successfully: {file_name}")
            self.update_download_file_path(full_file_path)
        except requests.exceptions.HTTPError as http_error:
            logger.error(f"HTTP error occurred: {http_error}")
        except requests.exceptions.ConnectionError as connection_error:
            logger.error(f"Connection error occurred: {connection_error}")
        except Exception as error:
            logger.error(f"An error occurred: {error}")

    def extract_zip_to_directory(
        self, extract_path: Path = None, delete_zip: bool = False
    ) -> None:
        if extract_path is None:
            extract_path = self.downloaded_file_path.parent

        logger.info(
            f"Attempting to extract zip {self.downloaded_file_path.stem} to {extract_path}"
        )
        with zipfile.ZipFile(self.downloaded_file_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
        logger.info(
            f"Succesfully extracted {self.downloaded_file_path.stem} to {extract_path}!"
        )

        if delete_zip:
            logger.info(f"Attempting to delete zip... {self.downloaded_file_path}")
            self.downloaded_file_path.unlink()
            logger.info(
                f"Successfully deleted {self.downloaded_file_path.stem}.zip from the system!"
            )


def main():
    # Get CLI args from argparse handler
    args = parse_cli_args()
    
    # Define default downlaod path, this method for handling Path object
    if args.download_target_dir is None:
        download_path = Path(__file__).resolve().parents[1] / "data" / "input"

    # Instantiate FileDownloader object instance with CLI args
    downloader = FileDownloader(url=args.url, download_target_dir=download_path, file_name=args.file_name, stream_downloads=args.stream_downloads)
    
    # Call instance method - Download file from URL attribute
    downloader.download_file_from_url()
    
    # Optionally call instance method - Extract zip file to directory
    if args.extract_zip:
        downloader.extract_zip_to_directory(delete_zip=args.delete_zip)


if __name__ == "__main__":
    main()
