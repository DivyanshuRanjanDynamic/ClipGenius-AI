from pytubefix import YouTube
from pytubefix.cli import on_progress

url1 = "https://www.youtube.com/watch?v=RDUjTleS3Hk&t=1s"
url2 = "https://www.youtube.com/watch?v=dlXt8CLb-PM&t=1s"

yt = YouTube(url1, on_progress_callback=on_progress)
print(yt.title)

ys = yt.streams.get_highest_resolution()
if ys is None:
    print("No stream found. Available streams:")
    print(yt.streams)
else:
    ys.download()
