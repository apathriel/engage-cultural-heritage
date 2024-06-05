import os
from pathlib import Path

from dotenv import load_dotenv
from hugchat import hugchat
from hugchat.login import Login

from logging_utils import get_logger

logger = get_logger(__name__)

 # Load environment variables from .env file
env_file_path = Path(__file__).resolve().parents[1] / "data" / "hf_creds.env"
load_dotenv(dotenv_path=env_file_path)

# Get environment variables for HF sign in
EMAIL = os.getenv("EMAIL")
PASSWD = os.getenv("PASSWORD")

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

desc_prompt = "Generer en fængende beskrivelse af fortidsminde udfra følgelde link. Formuler dig som om du er en ekspert inden for dansk kulturhistorie. Du bør altid inddrage fortidsmindets anlæg og datering. LINK: https://www.kulturarv.dk/fundogfortidsminder/Lokalitet/38484/Udskriv/"
rewrite_prompt = "Omskriv følgende tekst til en billedgenererings prompt. Behold kun det mest essentielle information, der beskriver visuelle elementer. TEKST:"

desc_message = chatbot.chat(desc_prompt, web_search=False)
logger.debug("Message sent to chatbot.")
desc_message.wait_until_done()

monument_description = desc_message.get_final_text()

rewrite_message = chatbot.chat(rewrite_prompt + monument_description, web_search=False)
logger.debug("Message sent to chatbot.")
rewrite_message.wait_until_done()

rewritten_description = rewrite_message.get_final_text()

print(rewritten_description)

print("Script completed")
