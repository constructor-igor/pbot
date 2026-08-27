import os
import logging
import re
import subprocess
import yt_dlp

#
# https://habr.com/ru/articles/870110/
#

class YoutubeDownloaderFix:
    def __init__(self):
        None
    def download(self, url, target_folder) -> int:
        return self.download_audio(url)
    def download_audio(self, link: str) -> int:
        logging.info(f"Download is starting for {link}")
        try:
            with yt_dlp.YoutubeDL({
                "format": "bestaudio/best",
                "noplaylist": True,
                "quiet": True,
            }) as downloader:
                info = downloader.extract_info(link, download=False)
                file_name = self.get_file_name(info["title"])
                downloader.params["outtmpl"] = {"default": file_name}
                out_file = downloader.prepare_filename(info)
                downloader.download([link])

            logging.info(f"Selected audio stream: {info['title']}")
            base, _ = os.path.splitext(out_file)
            mp3_file = base + ".mp3"

            ffmpeg_dir = r"D:\ig\myprojects\github\extract_text\data\ffmpeg-7.1.1\bin"
            os.environ["PATH"] += os.pathsep + ffmpeg_dir

            #192k
            subprocess.run([
                "ffmpeg", "-y", "-i", out_file,
                "-vn", "-ab", "128k", "-ar", "44100", "-f", "mp3", mp3_file
            ], check=True)

            # remove original file if you want
            os.remove(out_file)
            file_size = os.path.getsize(mp3_file) if os.path.exists(mp3_file) else 0
            logging.info("Download is completed successfully")
            return file_size
        except Exception as e:
            logging.exception("Download failed")
            return 0

    def get_file_name(self, title: str) -> str:
        safe = re.sub(r'[<>:"/\\|?*]', '_', title)
        return f"{safe}.mp4"
        # target_file = title.replace('?', '_')
        # target_file = target_file.replace('/', '_')
        # target_file = target_file.replace('"', '_')
        # target_filename = f"{target_file}.mp4"
        # return target_filename
