import requests

# URL of the Django endpoint
url = "http://127.0.0.1:8000"

# Path to the video file
video_file_path = r"C:\Users\Aleena Ajith\OneDrive\Desktop\DJANGO\park_video.mp4"

# Send the POST request with the video file
with open(video_file_path, 'rb') as video_file:
    files = {'video': video_file}
    response = requests.post(url, files=files)

# Check if the request was successful
if response.status_code == 200:
    detection_results = response.json()
    print(detection_results)
else:
    print(f"Request failed with status code: {response.status_code}")