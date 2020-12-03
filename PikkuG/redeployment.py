import os
import sys
import json
import time
import zipfile
import requests
from telco.nokia.cbamlibrary.src.CBAMLibrary import CBAMLibrary
from telco.openstack_foundation.openstacklibrary.OpenStackLibrary import OpenStackLibrary

artifactory_url = "https://artifactory.elisa.eficode.io"
artifactory_repository = "Nokia_TAS"
download_directory = "artifactory-download"
cbam_host = "1.1.1.1"
cbamlib = CBAMLibrary()
cbamlib.disable_insecure_request_warning()

def is_image_file(filename):
    extensions = ["qcow2", "iso", "img", "ova", "ploop", "vdi", "vhd", "vmdk", "aki", "ami", "ari"]
    for extension in extensions:
        if filename.endswith(f".{extension}"):
            return True
    return False

def init_cbam_connection():
    cbamlib.connect_to_cbam(host=cbam_host,
                            client_id=os.environ["CBAM_BOT_USR"],
                            client_secret=os.environ["CBAM_BOT_PSW"],
                            verify=False,
                            timeout=60)


# Parse names of VNFs that will be removed
try:
    vnf_names = map(lambda vnf: vnf.strip(), sys.argv[1].split(","))
except:
    raise ValueError("Couldn't parse vnf names. Names should be given as a string argument using a comma separator, "
                    + "example: python redeployment.py 'vnf1, vnf2'")

# Initialize CBAM connection
init_cbam_connection()

# Remove VNFs and VNFDs
vnfds = set()
for vnf_name in vnf_names:
    vnf = cbamlib.get_vnf_by_name(vnf_name)
    vnfds.add(vnf["vnfPkgId"])
    print(f"Terminating VNF {vnf['id']}")
    cbamlib.terminate_vnf(vnf["id"], termination_type="FORCEFUL")
    cbamlib.wait_until_vnf_is_terminated(vnf["id"], timeout=600)
    print(f"Deleting VNF {vnf['id']}")
    cbamlib.delete_vnf(vnf["id"])

for vnfd in vnfds:
    print(f"Deleting VNFD {vnfd}")
    cbamlib.delete_vnfd(vnfd)

# Upload VNFD zip to CBAM
for filename in os.listdir(download_directory):
    if "_mcs_" in filename:
        print(f"Onboarding VNFD '{filename}'")
        vnfd = cbamlib.onboard_vnfd(f"{download_directory}/{filename}")
        print(f"VNFD onboarded with id {vnfd['id']}")

print("Creating VNF")
vnfd = cbamlib.get_vnfd(vnfd['id'])
vnf = cbamlib.create_vnf(vnfd["vnfdId"], "NTAS2-HELPALAB3")
print(f"VNF created with id {vnf['id']}")

print("Modifying VNF")
# TODO: REPLACE HARDCODED FILENAMES
cbamlib.modify_vnf(vnf["id"], f"{download_directory}/extensions.json")

# Upload image to CBIS
oslib = OpenStackLibrary()
oslib.connect(cloud="name")

# TODO: web-import does not work with artifactory, download images using Jenkins artifactory plugin and upload them to CBIS with create image
#image_uri = f"https://{os.environ['NTAS_BOT_USR']}:{os.environ['NTAS_BOT_PSW']}@artifactory.eficode.io/Nokia_TAS/cirros-0.4.0-x86_64-disk.img"
#oslib.import_image("eficode-test", method="web-download", uri=image_uri, disk_format="qcow2", container_format="bare",
#                    visibility="private", md5="443b7623e27ecf03dc9e01ee93f67afe")

# Jenkins loads all zip-files from artifactory/INSTALL_MEDIA to artifactory-download directory, unzip and upload image files
for filename in os.listdir(download_directory):
    # Image zip file names contain variant identifier, either _OS_ for Openstack or _VM_ for VMware
    if "_OS_" in filename or "_VM_" in filename:
        with zipfile.ZipFile(f"{download_directory}/{filename}", "r") as zip_ref:
            print(f"Unzipping files to {download_directory}/{os.path.splitext(filename)[0]}")
            extract_path = f"{download_directory}/{os.path.splitext(filename)[0]}"
            zip_ref.extractall(extract_path)
            # Image zips contain other files as well, look for the image file
            for extracted in os.listdir(extract_path):
                if is_image_file(extracted):
                    image_name = os.path.splitext(extracted)[0]
                    print(f"Uploading image '{image_name}' to CBIS")
                    oslib.create_image(image_name, filename=f"{extract_path}/{extracted}", visibility="private")

# Re-initialize CBAM connection
init_cbam_connection()

# TODO: REPLACE HARDCODED FILENAMES
# Insert CBIS username and password to instantiation json
modified = ""
instantiation_json = open(f"{download_directory}/instantiation_data.json", "r+")
for line in instantiation_json:
    modified += line.replace("<username>", os.environ["OS_USERNAME"]).replace("<password>", os.environ["OS_PASSWORD"])
instantiation_json.seek(0)
instantiation_json.write(modified)
instantiation_json.truncate()
instantiation_json.close()

# TODO: REPLACE HARDCODED FILENAMES
print("Instantiating VNF")
cbamlib.instantiate_vnf(vnf["id"], f"{download_directory}/instantiation_data.json")
cbamlib.wait_until_vnf_is_instantiated(vnf["id"], timeout=4800, interval=30)

# Execute health check, sleep for 5 mins as there is no poller for health check status implemented
cbamlib.execute_custom_operation_on_vnf(vnf["id"], "vnf_health_check")
time.sleep(300)
