# Practice Case Task:
# Create a python script which can upload a file from the internet to Google Cloud Storage (Bonus point if
# you use Docker)

from google.cloud import storage
import urllib.request

BUCKET_NAME = "suryo-df8-bucket"

def upload_to_gcs(file_url, file_name):
    
    # Authenticate using .json key
    storage_client = storage.Client.from_service_account_json('suryo-df8-06052a7d7193.json')
    bucket = storage_client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(file_name) # You can add a folder directory by appending a directory path before file_name
    blob.upload_from_filename(file_name) # file_name needs to include file directory path from local
    ### Comment the rest of the function and uncomment the line above if you just want to upload from local ###

    # Try to read the URL
    try:
        with urllib.request.urlopen(file_url) as response:
            info = response.info()
            blob.upload_from_string(response.read(), content_type=info.get_content_type())
            print("Uploaded file from: " + file_url)

    except Exception:
        print('Could not upload file, exception: ' + traceback.format_exc())

# Main driver function
upload_to_gcs("https://file-examples.com/storage/fe7b2149a76383f20ac005f/2017/02/file-sample_100kB.docx", "docxtest.docx")
