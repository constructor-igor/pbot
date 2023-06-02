from pytube import YouTube

# YouTube video URL
video_url = "https://www.youtube.com/watch?v=3mZvCGk4XPQ"

# Create a YouTube object
yt = YouTube(video_url)

# Get the audio stream
audio_stream = yt.streams.filter(only_audio=True).first()

# Download the audio stream
audio_stream.download(output_path="path/to/save/directory", filename="audio")

print("Audio downloaded successfully.")