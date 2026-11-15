"""Issue temporary S3 role credentials on request.

The EC2 broker serves this endpoint locally through an SSH tunnel.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import boto3
from botocore.exceptions import BotoCoreError, ClientError


# ---------- HTTP endpoint ----------

class BrokerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Accept credential requests at one endpoint.
        if self.path != "/credentials":
            self.send_error(404)
            return

        # Use the EC2 role to request credentials for the S3 role.
        try:
            credentials = boto3.client("sts").assume_role(
                RoleArn=os.environ["S3_ROLE_ARN"], RoleSessionName="credential-broker"
            )["Credentials"]
        except (BotoCoreError, ClientError):
            self.send_error(502, "Unable to obtain credentials")
            return

        # Return the temporary credentials without allowing caches to store them.
        body = json.dumps(credentials, default=lambda value: value.isoformat()).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


# ---------- Server ----------

if __name__ == "__main__":
    # Require the target role and accept connections only from the instance.
    if not os.environ.get("S3_ROLE_ARN"):
        raise SystemExit("Set S3_ROLE_ARN before starting the broker")
    HTTPServer(("127.0.0.1", 8443), BrokerHandler).serve_forever()
