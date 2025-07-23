import logging

from dotenv import load_dotenv

from config.logging_config import setup_logging
from evaluator.kavak_agent_evaluator import run_kavak_evaluator
load_dotenv()

setup_logging()
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    run_kavak_evaluator()