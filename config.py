from __future__ import annotations
import os

_BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    SECRET_KEY: str          = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
    DATABASE_URI: str        = os.path.join(_BASE_DIR, "instance", "database.db")
    ML_API_URL: str          = os.environ.get("ML_API_URL", "https://burnout-api-rj45.onrender.com/predict")
    ML_API_TIMEOUT: int      = 30
    SURVEY_LIMIT_PER_DAY: int = 1
    DEBUG:   bool            = False
    TESTING: bool            = False
    RESULTS_RELEASE_HOUR:   int = 17
    RESULTS_RELEASE_MINUTE: int = 30


class DevelopmentConfig(BaseConfig):
    DEBUG: bool       = True
    DATABASE_URI: str = os.path.join(_BASE_DIR, "instance", "database_dev.db")
    ML_API_TIMEOUT: int = 30


class TestingConfig(BaseConfig):
    TESTING: bool    = True
    DEBUG:   bool    = True
    DATABASE_URI: str = ":memory:"
    WTF_CSRF_ENABLED: bool  = False
    ML_API_URL: str         = "https://burnout-api-rj45.onrender.com/predict"
    ML_API_TIMEOUT: int     = 2


class ProductionConfig(BaseConfig):
    DEBUG:   bool    = False
    TESTING: bool    = False
    DATABASE_URI: str = os.path.join(_BASE_DIR, "instance", "database.db")

    # These will be empty strings if not set; _validate_production_config()
    # raises at startup when running in production mode.
    SECRET_KEY: str  = os.environ.get("SECRET_KEY", "")
    ML_API_URL: str  = os.environ.get("ML_API_URL", "")


def _validate_production_config(app) -> None:
    for var in ("SECRET_KEY", "ML_API_URL"):
        if not app.config.get(var, "").strip():
            raise ValueError(
                f"[ProductionConfig] Required environment variable '{var}' is not set."
            )


config_map: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
