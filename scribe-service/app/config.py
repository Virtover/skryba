from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loads configuration of the application.

    When an instance of this class is created, its attributes are
    initialized using the values from both environment variables and
    the content of .env file.
    """

    postgres_host: str
    postgres_user: str
    postgres_password: str
    postgres_db: str
    device: str
    hf_token: str

    class Config:
        case_sensitive = False


settings = Settings()
