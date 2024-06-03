import mimetypes
from pathlib import Path
import re
import requests
from urllib.parse import unquote
import zipfile

from logging_utils import get_logger

logger = get_logger(__name__)


def download_file_from_url(
    url: str,
    download_target_dir: Path,
    file_name: str = None,
    stream_download: bool = False,
) -> None:
    logger.info(f"Attempting to download file from: {url}")
    try:
        logger.info("Sending GET request...")
        response = requests.get(url, stream=stream_download)
        response.raise_for_status()

        if file_name is None:
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

        full_file_path = download_target_dir / file_name
        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_file_path, "wb") as file:
            logger.info(f"Writing file to: {full_file_path}...")
            if stream_download:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out the keep-alive new chunks
                        file.write(chunk)
            else:
                file.write(response.content)

        logger.info(f"File downloaded successfully: {file_name}")
    except requests.exceptions.HTTPError as http_error:
        logger.error(f"HTTP error occurred: {http_error}")
    except requests.exceptions.ConnectionError as connection_error:
        logger.error(f"Connection error occurred: {connection_error}")
    except Exception as error:
        logger.error(f"An error occurred: {error}")

    return full_file_path


def extract_zip_to_directory(
    zip_path: Path, extract_path: Path = None, delete_zip: bool = False
) -> None:
    if extract_path is None:
        extract_path = zip_path.parent

    logger.info(f"Attempting to extract zip {zip_path.stem} to {extract_path}")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_path)
    logger.info(f"Succesfully extracted {zip_path.stem} to {extract_path}!")

    if delete_zip:
        logger.info(f"Attempting to delete zip... {zip_path}")
        zip_path.unlink()
        logger.info(f"Successfully deleted {zip_path.stem} from the system!")


def main():
    download_path = Path(__file__).resolve().parents[1] / "data"
    download_url = (
        "https://sciencedata.dk/shared/ce0f8e62af16dab66b45f13be90d00f8?download"
    )

    zip_download_path = download_file_from_url(
        url=download_url, download_target_dir=download_path
    )

    extract_zip_to_directory(zip_download_path, download_path, delete_zip=True)


if __name__ == "__main__":
    main()
