import mimetypes
from pathlib import Path
import re
import requests
from urllib.parse import unquote

from code_utilities import timing_decorator
from logging_utils import get_logger

logger = get_logger(__name__)

@timing_decorator(logger=logger)
def download_file_from_url(
    url: str, download_target_dir: Path, file_name: str = None,
) -> None:
    logger.info(f"Attempting to download file from: {url}")
    try:
        logger.info("Sending GET request...")
        response = requests.get(url)
        response.raise_for_status()

        if file_name is None:
            logger.info("No file name provided. Determining file name from response headers...")
            content_disposition = response.headers.get('Content-Disposition')

            # Trying to get the filename from Content-Disposition header, if fail try to infer from Content-Type with mimetypes
            if content_disposition:
                file_name = re.findall('filename="(.+)"', content_disposition)
                if file_name:
                    file_name = unquote(file_name[0])
                    logger.info(f"File name [{file_name}] sucessfully extracted from Content-Disposition header!")

            if file_name is None:
                content_type = response.headers['Content-Type']
                extension = mimetypes.guess_extension(content_type)
                file_name = f"data{extension}"
                logger.info(f"File name [{file_name}] sucessfully inferred from Content-Type header!")

        full_file_path = download_target_dir / file_name
        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(full_file_path, "wb") as file:
            logger.info(f"Writing file to: {full_file_path}...")
            file.write(response.content)

        logger.info(f"File downloaded successfully: {file_name}")
    except requests.exceptions.HTTPError as http_error:
        logger.error(f"HTTP error occurred: {http_error}")
    except requests.exceptions.ConnectionError as connection_error:
        logger.error(f"Connection error occurred: {connection_error}")
    except Exception as error:
        logger.error(f"An error occurred: {error}")




def main():
    download_path = Path(__file__).resolve().parents[1] / "data"
    download_url = "https://sciencedata.dk/shared/ce0f8e62af16dab66b45f13be90d00f8?download"

    download_file_from_url(url=download_url, download_target_dir=download_path)

if __name__ == "__main__":
    main()