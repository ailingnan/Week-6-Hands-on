import os
from dotenv import load_dotenv
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from utils.config_validator import validate_env
load_dotenv()

def get_sf_connection():
    """
    Centralized Snowflake connection using RSA key authentication.
    All modules should import and call this instead of duplicating sf_connect().
    """
  validate_env()

  key_path = os.getenv("SNOWFLAKE_RSA_KEY_PATH", "rsa_key.p8")
    if not os.path.exists(key_path):
        raise FileNotFoundError(
            f"Missing RSA key file: {key_path}. Set SNOWFLAKE_RSA_KEY_PATH or place rsa_key.p8 in repo root."
        )

    with open(key_path, "rb") as f:
        pk = serialization.load_pem_private_key(
            f.read(), password=None, backend=default_backend()
        )

    pkb = pk.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        private_key=pkb,
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA"),
    )
