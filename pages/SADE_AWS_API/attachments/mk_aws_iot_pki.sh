#!/usr/bin/env bash

set -e

echo "AWS IoT Certificate Request Generator"
echo "--------------------------------------"

read -rp "Name: " NAME
read -rp "Email address: " EMAIL
read -rp "Organization name or abbreviation: " ORG
read -rp "State (2-letter abbreviation): " STATE

# Extract local part of email
LOCAL_PART="${EMAIL%@*}"

KEY_FILE="${LOCAL_PART}.key"
CSR_FILE="${LOCAL_PART}.csr"

echo
echo "Generating private key..."
openssl ecparam -name prime256v1 -genkey -noout -out "$KEY_FILE"
chmod 600 "$KEY_FILE"

echo "Generating CSR..."
openssl req -new \
  -key "$KEY_FILE" \
  -out "$CSR_FILE" \
  -subj "/C=US/ST=${STATE}/O=${ORG}/CN=${LOCAL_PART}" \
  -addext "subjectAltName = email:${EMAIL}"

echo
echo "Done."
echo "Private key: $KEY_FILE (KEEP THIS SECRET)"
echo "CSR file:    $CSR_FILE (Send this to us)"