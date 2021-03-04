# icloud-photo-backup

Using `pyicloud`, this tool signs into your iCloud account and downloads all your photos into a folder `photos` in the current working directory. In a separate folder `albums`, it stores text files describing the content of each album through the contained photo IDs. This avoids duplicate files on disk. To match these to the files in the `photos` folder, a `photos.csv` is created in the working directory that has rows for `photo_id,original_filename,filename`.

The code is pretty straightforward, so you might have to adapt it for your particular use case.