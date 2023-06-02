import logging
import requests
from pytube import YouTube
import gdown
import youtube_dl

#
# https://www.freecodecamp.org/news/python-program-to-download-youtube-videos/
#

def download_high_resolution_mp4(link):
    youtubeObject = YouTube(link)
    youtubeObject = youtubeObject.streams.get_highest_resolution()
    try:
        youtubeObject.download()
    except:
        logging.error("An error has occurred")
    logging.info("Download is completed successfully")

def download(link):
    try:
        yt = YouTube(link)
        yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first().download()
    except:
        logging.error("An error has occurred")
    logging.info("Download is completed successfully")

def download_audio(link):
    logging.info(f"Download is starting for {link}")
    try:
        yt = YouTube(link)
        all_audio_streams = list(yt.streams.filter(only_audio=True).order_by('itag').desc())
        audio = all_audio_streams[-1]
        # audio.download(filename=f"{audio.title}.mp3")
        target_file = audio.title.replace('?', '_')
        target_file = target_file.replace('/', '_')
        audio.download(filename=f"{target_file}.mp3")
        # yt.streams.filter(only_audio=True).order_by('itag').desc().last().download()
    except Exception as e:
        logging.error(f"An error has occurred with error {str(e)}")
    logging.info("Download is completed successfully")

def download_from_google_drive(url, output):
    gdown.download(url, output, quiet=False)

def download_from_google_drive_2(file_id, output):
    from google_drive_downloader import GoogleDriveDownloader as gdd
    gdd.download_file_from_google_drive(file_id=file_id, dest_path=output, unzip=True)


def download_dl(url, target_file):
    # Set options for the YouTube downloader
    ydl_opts = {
        'format': 'bestaudio/best',  # Download the best audio quality available
        'outtmpl': target_file,  # Save the audio file as 'audio_file.mp3'
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Extract the audio from the downloaded file
            'preferredcodec': 'mp3',  # Convert the audio to MP3 format
            'preferredquality': '192',  # Set the audio quality to 192 kbps
        }],
    }
    # Create a YouTube downloader instance with the options
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        # Download the audio file
        ydl.download([url])

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"
    url = "https://drive.google.com/u/0/uc?id=16LcZF_k432bthFjCXpBc_sbdAmVx8AxX&export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

if __name__ == "__main__":
    file_id = 'TAKE ID FROM SHAREABLE LINK'
    destination = 'DESTINATION FILE ON YOUR DISK'
    download_file_from_google_drive(file_id, destination)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    # logging.info('This is an info message')
    links = ["https://www.youtube.com/watch?v=3mZvCGk4XPQ"]
    for link in links:
        download_audio(link)

    # download_file_from_google_drive("1ysViKgqDoCclwy48-mRZxuR7EmjemHRx", "rambam2023_2023_05_13.mp3")
