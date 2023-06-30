import logging
from pytube import YouTube


class YoutubeDownloader:
    def __init__(self):
        None
    def download(self, url, target_folder):
        self.download_audio(url)
    def download_audio(self, link):
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
