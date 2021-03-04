import base64
import os
import re
import shutil
import sys
import unicodedata

from pathlib import Path

from pyicloud import PyiCloudService


def main():
    api = signIn()

    os.makedirs("albums", exist_ok=True)
    albums = api.photos.albums
    albumCounter = 0
    for album in albums:
        if album in {"All Photos"}:
            continue

        albumCounter += 1
        filename = "albums/" + slugify(album, allow_unicode=True) + ".txt"

        print(f"Backing up album {albumCounter} / {len(albums) - 1} '{album}'...")
        backupAlbumMetadata(album, api, filename)
        print("Album backup complete.")

    os.makedirs("photos", exist_ok=True)
    allPhotos = api.photos.all

    with open("photos.csv", "w", encoding="utf-8") as photosDb:
        photosDb.write("photo_id,original_filename,filename")
        for photoIdx, photo in enumerate(allPhotos):
            print(f"Backing up photo {photoIdx + 1} / {len(allPhotos)}: {photo.filename}")
            ext = Path(photo.filename).suffix
            base64Id = str(base64.urlsafe_b64encode(photo.id.encode("utf-8")))
            filename = f"photos/{base64Id}{ext}"
            metaFilename = f"photos/{base64Id}.meta.txt"

            photosDb.write(f"{photo.id},{photo.filename},{base64Id}{ext}\n")

            with open(metaFilename, "x", encoding="utf-8") as metaFile:
                metaFile.write("id: ")
                metaFile.write(photo.id)
                metaFile.write("\noriginal_filename: ")
                metaFile.write(photo.filename)

            with photo.download() as download:
                with open(filename, "wb") as file:
                    shutil.copyfileobj(download.raw, file)


def backupAlbumMetadata(album, api, filename):
    with open(filename, "x", encoding="utf8") as file:
        file.write(album)
        file.write("\n\n")

        albumPhotos = api.photos.albums[album]
        for photoIdx, photo in enumerate(albumPhotos):
            file.write(photo.id + " " + photo.filename)
            file.write("\n")


def signIn():
    username = input("Enter your username: ")
    password = input(f"Enter the password for {username}: ")
    api = PyiCloudService(username, password)
    if api.requires_2fa:
        print("Two-factor authentication required.")
        code = input("Enter the code you received of one of your approved devices: ")
        result = api.validate_2fa_code(code)
        print("Code validation result: %s" % result)

        if not result:
            print("Failed to verify security code")
            sys.exit(1)

        if not api.is_trusted_session:
            print("Session is not trusted. Requesting trust...")
            result = api.trust_session()
            print("Session trust result %s" % result)

            if not result:
                print("Failed to request trust. You will likely be prompted for the code again in the coming weeks")
    elif api.requires_2sa:
        import click
        print("Two-step authentication required. Your trusted devices are:")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            print("  %s: %s" % (i, device.get('deviceName',
                                              "SMS to %s" % device.get('phoneNumber'))))

        device = click.prompt('Which device would you like to use?', default=0)
        device = devices[device]
        if not api.send_verification_code(device):
            print("Failed to send verification code")
            sys.exit(1)

        code = click.prompt('Please enter validation code')
        if not api.validate_verification_code(device, code):
            print("Failed to verify verification code")
            sys.exit(1)
    return api


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
