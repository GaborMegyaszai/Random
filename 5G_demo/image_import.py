import openstack, sys

openstack.enable_logging(True, stream=sys.stdout)

image_name = "ubuntu-14.04-server-cloudimg-amd64-disk1"
image_uri = "https://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img"
md5 = "72eec501d849cb834c8da0b21b295c66"
container_format = "bare"
image_format = "qcow2"
image_visibility = "public"

def create_connection():
    return openstack.connect(cloud="openstack")

def create_image():
    image_attributes = {
        "name": image_name,
        "disk_format": image_format,
        "md5": md5,
        "container_format": container_format,
        "visibility": image_visibility
    }
    image = connection.image.create_image(**image_attributes)
    return image

def add_image_location(image):
    body = [
        {
            "op": "add",
            "path": "/locations/1",
            "value": {
                "metadata": {},
                "url": image_uri
            }
        },
        # TODO: Image id is set as image name by default for some reason, changing it back here
        {
            "op": "replace",
            "path": "/name",
            "value": image_name
        }
    ]
    headers = {"Content-Type": "application/openstack-images-v2.1-json-patch"}
    res = connection.session.patch("/v2/images/" + image.id, json=body, headers=headers, endpoint_filter={"service_type": "image"})

def set_image_name(image, name):
    body = [{"op": "replace", "path": "/name", "value": name}]
    headers = {"Content-Type": "application/openstack-images-v2.1-json-patch"}
    connection.session.patch("/v2/images/" + image.id, json=body, headers=headers, endpoint_filter={"service_type": "image"})

def check_if_image_exists():
    """Checks if image with {image_name} already exists. Returns the image if it does exist and None if it doesn't. Existing image is renamed as {name}_old."""
    existing_image = connection.image.find_image(image_name)
    if existing_image:
        set_image_name(existing_image, image_name + "_old")
    return existing_image


print("Import image:")
connection = create_connection()
# TODO: Automatic image deletion is disabled since add image location is not used, re-enable this when it's back
#existing_image = check_if_image_exists()
existing_image = None

try:
    image = create_image()
    # TODO: Add image location is removed temporarily, re-enable it when openstack url-download works
    #add_image_location(image)
    if existing_image:
        connection.image.delete_image(existing_image)
# Revert changes if anything fails while creating the new image
except Exception as e:
    # Delete created image if it exists
    if "image" in locals() and image:
        connection.image.delete_image(image)
    # Restore the previous image if it exists
    if existing_image:
        set_image_name(existing_image, image_name)
    raise Exception("Creating new image failed: " + e.message) from e
