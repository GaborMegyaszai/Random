import requests, os, pathlib, dotenv, json, argparse
from requests.auth import HTTPBasicAuth

API_VERSION = "v1"
AUTH_USER = "openbatonOSClient"
AUTH_PASSWORD = "secret"

class APIHandler:
    
    def __init__(self, args):
        self.set_env_variables(args.rc_path)
        self.add_arguments(args)
        self.check_variables()
        self.retrieve_token()

    def set_env_variables(self, rc_path):
        env_path = pathlib.Path(rc_path)
        dotenv.load_dotenv(dotenv_path=env_path)
        ip_address = os.getenv("OB_NFVO_IP")
        port = os.getenv("OB_NFVO_PORT")
        self.api_entrypoint = "http://" + ip_address + ":" + port if ip_address and port else None
        self.username = os.getenv("OB_USERNAME")
        self.password = os.getenv("OB_PASSWORD")
        self.project_id = os.getenv("OB_PROJECT_ID")

    def add_arguments(self, args):
        """Override openbaton.rc values with argument values if they exist."""
        for arg in vars(args):
            if getattr(args, arg):
                setattr(self, arg, getattr(args, arg))

    def check_variables(self):
        """Check all required variables have been set and raise an exception if any are missing."""
        required_variables = ["api_entrypoint", "username", "password", "project_id"]
        missing_variables = []
        for variable in required_variables:
            if not getattr(self, variable):
                missing_variables.append(variable)
        if self.password=="$password" or self.password is None:
            raise TypeError("Password not set, use option --password to set it.")
        if missing_variables:
            raise TypeError("Missing required variables: " + ", ".join(missing_variables) + ". Use -h to see how these can be set.")

    def retrieve_token(self):
        body = "username=" + self.username + "&password=" + self.password + "&grant_type=password"
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        auth = HTTPBasicAuth(AUTH_USER, AUTH_PASSWORD)
        response = requests.post(self.api_entrypoint + "/oauth/token", data=body, headers=headers, auth=auth)
        if response.status_code != 200:
            if response.status_code == 400:
                raise Exception("Authentication failed: " + response.json()["detailMessage"])
            raise Exception("Unexpected HTTP response status: " + str(response.status_code))
        self.token = response.json()["value"]

    def request(self, method, path, **kwargs):
        url = self.api_entrypoint + "/api/" + API_VERSION + path
        headers = {"Authorization": "Bearer " + self.token}
        if "headers" in kwargs:
            headers.update(kwargs.get("headers"))
        kwargs["headers"] = headers
        return getattr(requests, method)(url, **kwargs)

    def get(self, path, **kwargs):
        return self.request("get", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("post", path, **kwargs)


def upload_nsd(nsd_file):
    contents = open(nsd_file, "rb").read()
    headers = {"Content-Type": "application/json", "project-id": api_handler.project_id}
    response = api_handler.post("/ns-descriptors", data=contents, headers=headers)
    nsd_id = get_created_id(response)
    print("Created new Network Service Descriptor with ID", nsd_id)
    return nsd_id

def deploy_nsd(nsd_id):
    headers = {"Content-Type": "application/json", "project-id": api_handler.project_id}
    response = api_handler.post("/ns-records/" + nsd_id, headers=headers)
    nsr_id = get_created_id(response)
    print("Deployed NSD", nsd_id, "with Network Service Record ID", nsr_id)

def get_created_id(response):
    """Convenience method for upload and deploy responses. Returns id from response if status is 201 Created."""
    if response.status_code != 201:
        raise Exception("Unexpected HTTP response status: " + str(response.status_code))
    return response.json()["id"]
    
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("nsd_path", help="Path to json file containing NSD configuration")
    parser.add_argument("--rc_path", default="./openbaton.rc", help="Path to openbaton.rc file, defaults to ./openbaton.rc. If overlapping arguments are given the values in rc file are overridden.", metavar="")
    parser.add_argument("--api_entrypoint", help="OpenBaton URL, e.g. 'http://localhost:8080'", metavar="")
    parser.add_argument("--username", help="OpenBaton username", metavar="")
    parser.add_argument("--password", help="OpenBaton password", metavar="")
    parser.add_argument("--project_id", help="OpenBaton project ID", metavar="")
    return parser.parse_args()

args = parse_args()
api_handler = APIHandler(args)
nsd_id = upload_nsd(args.nsd_path)
deploy_nsd(nsd_id)