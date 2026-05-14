import requests


# Specify the paths client cert, and private key.
CLIENT_CERT = "./user123.crt"
PRIVATE_KEY = "./user123.key"


# Make a Session to enable mTLS across multiple requests.
session = requests.Session()

# The server will present a publicly trusted certificate, so we can let the library verify it.
session.verify = True # This is True by default, but we set it explicitly here for clarity.

# The client certificate and private key are used for mTLS authentication.
session.cert = (CLIENT_CERT, PRIVATE_KEY)

response = session.get("https://api.sadezone.org/health")
print("Response 1:")
print(response.status_code)
print(response.json())
