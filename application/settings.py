"""
settings.py

Configuration for Flask app

Important: Place your secret keys and other private settings 
in the private_settings.py module, which should be kept out of version control.

"""

import private_settings

class Config(object):
    GOOGLE_CLOUD_PROJECT_ID = private_settings.GOOGLE_CLOUD_PROJECT_ID
    BIGDATA_QUERIES = private_settings.BIGDATA_QUERIES

class Development(Config):
    ENV = "DEV"

class Testing(Config):
    ENV = "TEST"

class Production(Config):
    ENV = "PROD"