import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

TZ = "America/Los_Angeles"


class Config:
    """
    Configuration class for handling application settings.
    """

    def __init__(self):
        self.load_env()
        self.setup_database()

    def load_env(self):
        """
        Load environment variables from .env file.
        """
        load_dotenv()
        self.SECRET_KEY = os.getenv("SECRET_KEY")
        self.ALGORITHM = os.getenv("ALGORITHM")
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 120))
        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")
        self.IS_ALLOWED_CREDENTIALS = os.getenv("IS_ALLOWED_CREDENTIALS", "False").lower() == "true"
        self.ALLOWED_METHODS = os.getenv("ALLOWED_METHODS", "").split(",")
        self.ALLOWED_HEADERS = os.getenv("ALLOWED_HEADERS", "").split(",")
        self.INVOICE_UPLOAD_DIR = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            "Invoices",
        )
        self._validate_env()

    def _validate_env(self):
        """
        Ensure that critical environment variables are not missing.
        """
        if not self.SECRET_KEY:
            raise ValueError("No SECRET_KEY found in environment variables")
        if not self.ALGORITHM:
            raise ValueError("No ALGORITHM found in environment variables")
        if not self.ALLOWED_ORIGINS:
            raise ValueError("No ALLOWED_ORIGINS found in environment variables")
        if not self.ALLOWED_METHODS:
            raise ValueError("No ALLOWED_METHODS found in environment variables")
        if not self.ALLOWED_HEADERS:
            raise ValueError("No ALLOWED_HEADERS found in environment variables")

    def setup_database(self):
        """
        Setup database connection and engine.
        """
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("No DATABASE_URL found in environment variables")
        self.test_database_url = os.getenv("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
        # Create database engine
        self.engine = create_engine(self.database_url, echo=True)


config_env = Config()
