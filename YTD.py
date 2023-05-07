from pytube import YouTube
from PIL import Image
from io import BytesIO
import pytube.request
import customtkinter as ctk
import urllib.request
import threading


# https://www.youtube.com/watch?v=Yw6u6YkTgQ4 short
# 9MB chunk size       1048576  1MB chunk size
pytube.request.default_range_size = 2097152

vid_link = " "
last_link = " "

# FUNCTIONS


def download_video():
    vid_link = link.get()
    try:
        yt = YouTube(vid_link, on_progress_callback=on_progress)
        video = yt.streams.get_highest_resolution()
        video.download()

    except Exception as e:
        print(e)


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    per = str(int(percentage_of_completion))
    pPercentage.configure(text=per + "%")
    print(per)
    pPercentage.update()

    progressBar.set(float(percentage_of_completion / 100))


def is_yturl():
    vid_link = link.get()
    if "https://www.youtube.com/watch?v=" in vid_link and len(vid_link) > 32:

        print("is url")

        yt = YouTube(vid_link)

        title.configure(text=yt.title)

        author.configure(text="by " + yt.author)

        try:
            u = urllib.request.urlopen(yt.thumbnail_url)
            raw_data = u.read()
            u.close()

            im = Image.open(BytesIO(raw_data))
            final_image = ctk.CTkImage(dark_image=im, size=(350, 197))

            thumbnail.configure(image=final_image)
            thumbnail.image = final_image

        except Exception as e:
            print(e)

        return True

    else:
        print("not url")
        return False


def check_url():
    global vid_link
    global last_link
    vid_link = link.get()

    if vid_link != last_link:
        threading.Thread(target=is_yturl).start()

    last_link = vid_link
    app.after(2000, check_url)


def start_download():
    thread_names = [t.name for t in threading.enumerate()]

    if "download_thread" not in thread_names:
        download_thread = threading.Thread(
            target=download_video, name="download_thread")
        download_thread.start()

# UI START


app = ctk.CTk()
app.geometry("720x480")
app.title("YouTube Downloader")
ctk.set_appearance_mode("System")

title = ctk.CTkLabel(app, font=("Roboto", 20), text="Insert YouTube link")
title.pack(pady=(5, 0))

author = ctk.CTkLabel(app, font=("Roboto", 15), text="")
author.pack()

thumbnail = ctk.CTkLabel(app, text="")
thumbnail.pack()

link = ctk.CTkEntry(app, width=350, height=40, placeholder_text="Youtube URL")
link.pack(pady=5)

pPercentage = ctk.CTkLabel(app, text="")
pPercentage.pack()

progressBar = ctk.CTkProgressBar(app, width=400)
progressBar.set(0)
progressBar.pack()

btn = ctk.CTkButton(app, fg_color="red", hover_color="darkred", font=("Roboto", 20),
                    text="Download", command=start_download, height=50)
btn.pack(padx=10, pady=10)


app.after(2000, check_url)  # run this function again 2,000 ms from now
app.mainloop()
