#!/var/www/fgo-solomon-stats/.venv/bin/python
from imgurpython import ImgurClient
import subprocess
from datetime import datetime
import json

base_path = "/var/www/fgo-solomon-stats/output/"

file_list = [
    "all_kps.png",
    "all_kps_except_barbatos.png",
    "all_kills_counts.png",
    "barbatos.png",
    "forneus.png",
    "flauros.png",
    "sabnock.png",
    "halphas.png",
    "andromalius.png",
    "amon_ra.png",
]
file_list = [base_path + file for file in file_list]

with open("imgur-api.json", "r") as f:
    account_credentials = json.load(f)

client_id = account_credentials["client_id"]
client_secret = account_credentials["client_secret"]
access_token = account_credentials["access_token"]
refresh_token = account_credentials["refresh_token"]


def imgur_upload():
    client = ImgurClient(client_id, client_secret, access_token, refresh_token)

    albums = client.get_album_images("OKG9U3G")

    current_image_id = [image.id for image in albums]

    new_image_id = []
    for file in file_list:
        #        with open(os.devnull, "w") as f:
        #            subprocess.call(["ect", file], stdout=f)
        #        shutil.copy2(file, "/var/www/fgo.square.ovh/solomon-raid-stats/")
        id = client.upload_from_path(file, anon=False)["id"]
        new_image_id.append(id)
    print("{}: Uploaded to imgur".format(datetime.now()))

    for id in current_image_id:
        client.album_remove_images("OKG9U3G", id)

    for id in new_image_id:
        client.album_add_images("OKG9U3G", id)
    print("{}: Editted album".format(datetime.now()))


imgur_upload()
