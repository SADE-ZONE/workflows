## Overview

To connect to the SADE AWS IoT Core Instance, you need three files:
- the CA's certificate file ([here is the download link for `CAs.crt`](attachments/CAs.crt))
- a private key
- a certificate (with your public key)

This is the best way to get a private key and a certificate:

1. You generate a private key locally (this stays on your machine).
2. You generate a Certificate Signing Request (CSR) using that key.
3. You send us the CSR (a `.csr` file).
4. We upload the CSR to AWS to create a signed certificate (a `.crt` file).
5. We send you the signed certificate (the `.crt` file).

This way your private key never leaves your machine.

This document describes three ways to create the private key and the CSR. **You only need to do this once.** Choose whichever method works best for you.

But before proceeding, make sure you have `openssl` installed. All three methods require `openssl`. On macOS:
```bash
brew install openssl
```
On Linux, `openssl` is usually pre-installed. On Ubuntu:
```bash
apt install openssl
```

---

## Option 1: Web Command Generator (Easiest)

We created a web page that generates the `openssl` commands for you. You enter your details in the form, and the page will output the corresponding bash commands.

The web page is 100% client-side. Your details are never sent anywhere. The JavaScript runs locally in your browser. Your input is only used to construct the commands displayed on the page.

1. Navigate to: https://mm-public-fileshare.s3.us-west-2.amazonaws.com/pki-cmd-wizzard.html
2. Enter your first name, last name, email, organization (e.g. your university name), and state. The page auto-updates a bash snippet as you type.
3. Open a terminal and `cd` to the directory where you want to save your key and CSR files.
4. Copy and paste the commands into the terminal and run them.

The generated commands will look something like this:

```bash
openssl ecparam -name prime256v1 -genkey -noout -out me.key

openssl req -new \
  -key me.key \
  -out me.csr \
  -subj "/C=US/ST=CALIFORNIA/O=Example University/CN=FIRST_NAME LAST_NAME" \
  -addext "subjectAltName = email:me@example.com"

chmod 600 me.key
```

---

## Option 2: Bash Script

We created a bash script that prompts you for your details and generates the private key and CSR.

[source code link](attachments/mk_aws_iot_pki.sh)

First, `cd` to the directory where you want to save your key and CSR files. Then download and run the script:

```bash
# download the script (macOS)
curl -o mk_aws_iot_pki.sh https://gist.githubusercontent.com/murphym18/2793b6dd3dd262dda21df655afbf0270/raw/dba344899c32e20635d318143dfdde23cecb8cf4/mk_aws_iot_pki.sh

# download the script (Linux)
wget https://gist.githubusercontent.com/murphym18/2793b6dd3dd262dda21df655afbf0270/raw/dba344899c32e20635d318143dfdde23cecb8cf4/mk_aws_iot_pki.sh

# run the script
bash mk_aws_iot_pki.sh
```

---

## Option 3: Manual Setup

> **Heads up:** There's no advantage to this approach over Option 1. These are the same commands the web page generates. But here you fill in the placeholders yourself, which is tedious and error prone. Unless you have a specific reason to do it manually, use Option 1 instead. That said, Feel free to read through this if you're curious about what the commands are doing.

First, `cd` to the directory where you want to save your key and CSR files.

Generate a private key and update the file permissions:
```bash
openssl ecparam -name prime256v1 -genkey -noout -out private.key
chmod 400 private.key
```

Generate a Certificate Signing Request (CSR):
```bash
openssl req -new \
  -key private.key \
  -out YOUR_EMAIL_LOCAL_PART.csr \
  -subj "/C=US/ST=YOUR_STATE/O=YOUR_ORG/CN=YOUR_FIRST_NAME YOUR_LAST_NAME" \
  -addext "subjectAltName = email:YOUR_EMAIL"
```

Replace the placeholders:
- `YOUR_EMAIL_LOCAL_PART` — the part of your email address before the `@`. For example, if your email is `user123@example.com`, use `user123`.
- `YOUR_STATE` — your state name (e.g. `Indiana`, `Missouri`, `California`).
- `YOUR_ORG` — your organization name, such as your university (e.g. `Notre Dame`, `SLU`).
- `YOUR_FIRST_NAME YOUR_LAST_NAME` — your name.
- `YOUR_EMAIL` — your email address (e.g. `user123@example.com`).

---

## Next Steps

Once you have your `.csr` file, please send it to us. We'll use it to generate your certificate and send it back to you.

Also, if you haven't already, download the CA certificate file: [CAs.crt](attachments/CAs.crt). You'll need this file along with your private key and certificate to connect to the SADE AWS IoT Core endpoint.

## How to connect with python and `paho-mqtt`

First make sure you have paho:
```bash
pip install paho-mqtt
```

Then take a look at the example: [attachments/mqtt_example.py](attachments/mqtt_example.py)

## How to connect using mosquitto_sub and mosquitto_pub

```bash
CA_FILE="./CAs.crt"
CLIENT_CERT="./user123.crt"
PRIVATE_KEY="./user123.key"

mosquitto_sub \
  -h "a3dpdfmwa109lg-ats.iot.us-east-2.amazonaws.com" \
  -p 8883 \
  --cafile ./CAs.crt \
  --cert ./user123.crt \
  --key ./user123.key \
  -i "EXAMPLE_MOS_SUB-123" \
  -t test/example


mosquitto_pub \
  -h "a3dpdfmwa109lg-ats.iot.us-east-2.amazonaws.com" \
  -p 8883 \
  -i "EXAMPLE-CLIENT_pub" \
  --cafile CAs.crt \
  --cert user123.crt \
  --key user123.key \
  --keyform pem \
  -t test/example \
  -m "hello world"
```