"""
settings.py

Configuration for Flask app

Important: Place your secret keys and other private settings
in the private_settings.py module, which should be kept out of version control.

"""

from application import private_settings

class Config(object):
    """Base class for a configuration object."""
    GOOGLE_CLOUD_PROJECT_ID = private_settings.GOOGLE_CLOUD_PROJECT_ID
    BIGQUERY_DATASET_ID = private_settings.BIGQUERY_DATASET_ID
    BQ_QUERIES = private_settings.BQ_QUERIES
    GCS_BUCKET_NAME = private_settings.GCS_BUCKET_NAME

class Development(Config):
    """Development specific configuration."""
    ENV = "DEV"

class Testing(Config):
    """Testing specific configuration."""
    ENV = "TEST"

class Production(Config):
    """Production specific configuration."""
    ENV = "PROD"
