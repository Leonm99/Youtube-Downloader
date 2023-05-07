from pytube import YouTube
from PIL import Image
from io import BytesIO
from textwrap import shorten
from time import strftime
from time import gmtime
import pytube.request
import customtkinter as ctk
import urllib.request
import threading


# lower pytube download chunk size so the progressbar updates more frequent
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

        title.configure(text=shorten(yt.title, width=40))
        author.configure(text="by: " + yt.author)
        views.configure(text="views: " + str(yt.views))
        duration.configure(text="duration: " +
                           strftime("%H:%M:%S", gmtime(yt.length)))

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
app.resizable(False, False)
app.title("YouTube Downloader")
app.grid_columnconfigure(0, minsize=350)
ctk.set_appearance_mode("System")

placeholder_image = ctk.CTkImage(
    Image.open("placeholder.png"), size=(350, 197))
thumbnail = ctk.CTkLabel(app, text="", image=placeholder_image)
thumbnail.grid(column=0, row=0, padx=5, pady=5)


video_info = ctk.CTkFrame(app, width=350)
video_info.grid(column=1, row=0, sticky="nsew", padx=5, pady=5)
video_info.grid_propagate(False)

title = ctk.CTkLabel(video_info, font=("Roboto", 20), text="")
title.grid(column=0, row=0, padx=5, pady=(5, 0), sticky="w")

author = ctk.CTkLabel(video_info, font=("Roboto", 15), text="")
author.grid(column=0, row=1, padx=5, sticky="w")

views = ctk.CTkLabel(video_info, font=("Roboto", 15), text="")
views.grid(column=0, row=2, padx=5, sticky="w")

duration = ctk.CTkLabel(video_info, font=("Roboto", 15), text="")
duration.grid(column=0, row=3, padx=5, sticky="w")


link = ctk.CTkEntry(app, width=350, height=40, placeholder_text="Youtube URL")
link.grid(column=0, row=2, columnspan=2, pady=(10, 0))

btn = ctk.CTkButton(app, fg_color="red", hover_color="darkred", font=("Roboto", 20),
                    text="Download", command=start_download, height=50)
btn.grid(column=0, row=3, columnspan=2, pady=(10, 0))

pPercentage = ctk.CTkLabel(app, text="")
pPercentage.grid(column=0, row=4, columnspan=2)

progressBar = ctk.CTkProgressBar(app, width=300)
progressBar.set(0)
progressBar.grid(column=0, row=5, columnspan=2)

app.after(2000, check_url)  # run this function again 2,000 ms from now
app.mainloop()
