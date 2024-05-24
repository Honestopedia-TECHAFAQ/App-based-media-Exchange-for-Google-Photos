import requests
import json
import os
import streamlit as st

class ConnectionProvider:
    def __init__(self, access_token):
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def authenticate(self):
        pass

    def index(self, params={}):
        pass

    def upload(self, file_path, params={}):
        pass

    def download(self, file_id, params={}):
        pass

    def delete(self, file_id, params={}):
        pass

class GooglePhotosProvider(ConnectionProvider):
    def __init__(self, access_token):
        super().__init__(access_token)
        self.base_url = 'https://photoslibrary.googleapis.com/v1'

    def index(self, params={}):
        url = f"{self.base_url}/mediaItems"
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def upload(self, file_path, params={}):
        upload_url = 'https://photoslibrary.googleapis.com/v1/uploads'
        with open(file_path, 'rb') as file:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/octet-stream',
                'X-Goog-Upload-File-Name': os.path.basename(file_path),
                'X-Goog-Upload-Protocol': 'raw',
            }
            response = requests.post(upload_url, headers=headers, data=file)
            if response.status_code == 200:
                upload_token = response.text
                create_url = f"{self.base_url}/mediaItems:batchCreate"
                payload = json.dumps({
                    "newMediaItems": [
                        {
                            "description": params.get('description', ''),
                            "simpleMediaItem": {
                                "uploadToken": upload_token
                            }
                        }
                    ]
                })
                response = requests.post(create_url, headers=self.headers, data=payload)
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Error: {response.status_code}, {response.text}")
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")

    def download(self, file_id, params={}):
        url = f"{self.base_url}/mediaItems/{file_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            media_item = response.json()
            download_url = media_item['baseUrl'] + '=d'
            download_response = requests.get(download_url)
            if download_response.status_code == 200:
                file_name = params.get('file_name', f"{file_id}.jpg")
                with open(file_name, 'wb') as file:
                    file.write(download_response.content)
                return file_name
            else:
                raise Exception(f"Error: {download_response.status_code}, {download_response.text}")
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def delete(self, file_id, params={}):
        url = f"{self.base_url}/mediaItems/{file_id}"
        response = requests.delete(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def create_album(self, album_title, params={}):
        url = f"{self.base_url}/albums"
        payload = json.dumps({
            "album": {"title": album_title}
        })
        response = requests.post(url, headers=self.headers, data=payload)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def get_album(self, album_id, params={}):
        url = f"{self.base_url}/albums/{album_id}"
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def list_albums(self, params={}):
        url = f"{self.base_url}/albums"
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

class InstagramProvider(ConnectionProvider):
    def __init__(self, access_token):
        super().__init__(access_token)
        self.base_url = 'https://graph.instagram.com'

    def index(self, params={}):
        url = f"{self.base_url}/me/media"
        response = requests.get(url, headers=self.headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def upload(self, file_path, params={}):
        raise NotImplementedError("Instagram API does not support direct upload of media.")

    def download(self, file_id, params={}):
        url = f"{self.base_url}/{file_id}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            media_item = response.json()
            media_url = media_item.get('media_url')
            if media_url:
                download_response = requests.get(media_url)
                if download_response.status_code == 200:
                    file_extension = media_url.split('.')[-1]
                    file_name = params.get('file_name', f"{file_id}.{file_extension}")
                    with open(file_name, 'wb') as file:
                        file.write(download_response.content)
                    return file_name
                else:
                    raise Exception(f"Error: {download_response.status_code}, {download_response.text}")
            else:
                raise Exception("Media URL not found in response.")
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")

    def delete(self, file_id, params={}):
        raise NotImplementedError("Instagram API does not support deleting media.")

# Streamlit UI
st.title("App-based-media-Exchange-for-Google-Photos")

selected_provider = st.selectbox("Select Provider", ["Google Photos", "Instagram"])

if selected_provider == "Google Photos":
    google_photos_token = st.text_input("Google Photos Access Token", type="password")
    provider = GooglePhotosProvider(google_photos_token)

elif selected_provider == "Instagram":
    instagram_token = st.text_input("Instagram Access Token", type="password")
    provider = InstagramProvider(instagram_token)

operation = st.selectbox("Select Operation", ["Index", "Upload", "Download", "Delete", "Create Album", "Get Album", "List Albums"])

if operation == "Index":
    params = st.text_area("Params (JSON)", "{}")
    if st.button("Execute"):
        try:
            response = provider.index(json.loads(params))
            st.json(response)
        except Exception as e:
            st.error(f"Error: {e}")

elif operation == "Upload":
    file = st.file_uploader("Choose a file")
    description = st.text_input("Description")
    if file and st.button("Upload"):
        try:
            file_path = os.path.join("/tmp", file.name)
            with open(file_path, "wb") as f:
                f.write(file.read())
            response = provider.upload(file_path, {"description": description})
            st.json(response)
        except Exception as e:
            st.error(f"Error: {e}")

elif operation == "Download":
    file_id = st.text_input("File ID")
    file_name = st.text_input("Save as", "downloaded_file.jpg")
    if st.button("Download"):
        try:
            provider.download(file_id, {"file_name": file_name})
            st.success(f"File downloaded as {file_name}")
        except Exception as e:
            st.error(f"Error: {e}")

elif operation == "Delete":
    file_id = st.text_input("File ID")
    if st.button("Delete"):
        try:
            response = provider.delete(file_id)
            st.json(response)
        except Exception as e:
            st.error(f"Error: {e}")

elif operation == "Create Album":
    album_title = st.text_input("Album Title")
    if st.button("Create Album"):
        try:
            response = provider.create_album(album_title)
            st.json(response)
        except Exception as e:
            st.error(f"Error: {e}")

elif operation == "Get Album":
    album_id = st.text_input("Album ID")
    if st.button("Get Album"):
        try:
            response = provider.get_album(album_id)
            st.json(response)
        except Exception as e:
            st.error(f"Error: {e}")

elif operation == "List Albums":
    params = st.text_area("Params (JSON)", "{}")
    if st.button("List Albums"):
        try:
            response = provider.list_albums(json.loads(params))
            st.json(response)
        except Exception as e:
            st.error(f"Error: {e}")

if __name__ == '__main__':
    google_photos_token = 'YOUR_GOOGLE_PHOTOS_ACCESS_TOKEN'
    instagram_token = 'YOUR_INSTAGRAM_ACCESS_TOKEN'

    google_photos_provider = GooglePhotosProvider(google_photos_token)
    instagram_provider = InstagramProvider(instagram_token)

    try:
        print(google_photos_provider.index())
        google_photos_provider.upload('path/to/your/photo.jpg', {'description': 'Test photo'})
        google_photos_provider.download('MEDIA_ITEM_ID', {'file_name': 'downloaded_photo.jpg'})
        google_photos_provider.delete('MEDIA_ITEM_ID')
        google_photos_provider.create_album('Test Album')
        print(google_photos_provider.get_album('ALBUM_ID'))
        print(google_photos_provider.list_albums())
    except Exception as e:
        print(f"Google Photos Error: {e}")

    try:
        print(instagram_provider.index())
        instagram_provider.download('MEDIA_ITEM_ID', {'file_name': 'downloaded_photo.jpg'})
    except Exception as e:
        print(f"Instagram Error: {e}")
