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

VIDEO_SAVE_DIRECTORY = "./Videos"
AUDIO_SAVE_DIRECTORY = "./Audio"
# FUNCTIONS

# Downloads the video and adds it to the download list afterwards


def download_video():
    vid_link = link.get()
    if is_yturl():

        progressBar.grid(column=1, row=2, columnspan=2, pady=5)
        pPercentage.grid(column=1, row=3, columnspan=2)

        try:
            yt = YouTube(vid_link, on_progress_callback=on_progress)
            video = yt.streams.get_highest_resolution()
            video.download(VIDEO_SAVE_DIRECTORY)

            final_image = get_thumbnail(yt.thumbnail_url, 125, 70)

            last_downloaded_video = ctk.CTkLabel(scrollable_frame, font=("Roboto", 20), text="  " + shorten(
                yt.title, width=70) + " by: " + yt.author, image=final_image, compound='left')
            last_downloaded_video.pack(padx=5, pady=5)

            reset_after_download()

        except Exception as e:
            print(e)

# Sets the current progress in the UI


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    per = str(int(percentage_of_completion))
    pPercentage.configure(text=per + "%")
    print(per)
    pPercentage.update()

    progressBar.set(float(percentage_of_completion / 100))

# CHecks if link is a usable YT link (this needs some refinement!)


def is_yturl():
    vid_link = link.get()

    if "https://www.youtube.com/watch?v=" in vid_link and len(vid_link) > 42:

        print("is url")

        yt = YouTube(vid_link)

        try:

            final_image = get_thumbnail(yt.thumbnail_url, 350, 197)

            thumbnail.configure(image=final_image, font=("Roboto", 20), compound='top',
                                text=shorten(yt.title, width=70) + " by: " + yt.author + "\nduration: " +
                                strftime("%H:%M:%S", gmtime(yt.length)) + " | views: " + f'{yt.views:,d}')
            thumbnail.image = final_image

        except Exception as e:
            print(e)

        return True

    else:
        print("not url")
        thumbnail.configure(text="", image=placeholder_image)
        return False

# Checks entry box


def check_entry():
    global vid_link
    global last_link
    vid_link = link.get()

    if vid_link != last_link:
        threading.Thread(target=is_yturl).start()

    last_link = vid_link
    app.after(2000, check_entry)

# Starts the download thread if not already started


def start_download():

    thread_names = [t.name for t in threading.enumerate()]

    if "download_thread" not in thread_names:
        download_thread = threading.Thread(
            target=download_video, name="download_thread")
        download_thread.start()

# Resets the state after download


def reset_after_download():
    thumbnail.configure(text="", image=placeholder_image)
    progressBar.set(0)
    progressBar.grid_forget()
    pPercentage.configure(text="")
    pPercentage.grid_forget()
    link.delete(0, ctk.END)

# Gets the thumbnail out of a link and returns it as a CTkImage


def get_thumbnail(link, x, y):
    u = urllib.request.urlopen(link)
    raw_data = u.read()
    u.close()

    im = Image.open(BytesIO(raw_data))
    final_image = ctk.CTkImage(dark_image=im, size=(x, y))

    return final_image


# UI START
app = ctk.CTk()
app.geometry("720x570")
app.resizable(False, False)
app.title("YouTube Downloader")
ctk.set_appearance_mode("System")

# Image to display when no video thumbnail is available
placeholder_image = ctk.CTkImage(
    Image.open("placeholder.png"), size=(350, 197))

# Frame for video info and progress indicators
video_info_frame = ctk.CTkFrame(app)
video_info_frame.grid(column=0, row=0,
                      sticky="nsew", columnspan=2, padx=5, pady=5)
video_info_frame.columnconfigure(2, weight=1)

thumbnail = ctk.CTkLabel(video_info_frame, text="", image=placeholder_image)
thumbnail.grid(column=1, row=0, columnspan=2, padx=5, pady=5, sticky="nsew")

pPercentage = ctk.CTkLabel(video_info_frame, text="")
progressBar = ctk.CTkProgressBar(video_info_frame, width=300)
progressBar.set(0)


# Frame for link entry and download button
input_frame = ctk.CTkFrame(app)
input_frame.grid(column=0, row=2, columnspan=2,
                 sticky="nsew", padx=5, pady=5)
input_frame.columnconfigure(3, weight=1)
input_frame.rowconfigure(1, weight=1)

link = ctk.CTkEntry(input_frame, width=550, height=40,
                    placeholder_text="Youtube URL")
link.grid(column=0, row=0, padx=5, pady=5)
link.configure(justify="center")

btn = ctk.CTkButton(input_frame, fg_color="red", hover_color="darkred", font=("Roboto", 20),
                    text="Download", command=start_download, height=50)
btn.grid(column=2, row=0, padx=5, pady=5, sticky="e")


# Frame for download list
scrollable_frame = ctk.CTkScrollableFrame(app, label_text="Downloaded:")
scrollable_frame.grid(column=0, row=3, columnspan=2,
                      sticky="nsew", padx=5, pady=5)


app.after(2000, check_entry)  # run this function again 2,000 ms from now
app.mainloop()
