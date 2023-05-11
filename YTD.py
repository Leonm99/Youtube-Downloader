from pytube import YouTube
from PIL import Image
from io import BytesIO
from textwrap import shorten
from time import strftime
from time import gmtime
from moviepy.editor import VideoFileClip, AudioFileClip
from time import sleep
import pytube.request
import customtkinter as ctk
import urllib.request
import threading
import requests
import re
import ffmpeg

# lower pytube download chunk size so the progressbar updates more frequent
pytube.request.default_range_size = 2097152

vid_link = " "
last_link = " "
resolutions = ("2160p", "1440p", "1080p", "720p",
               "480p", "360p", "240p", "144p")
paddings = {'padx': 5, 'pady': 5}


VIDEO_SAVE_DIRECTORY = "./Videos/"
AUDIO_SAVE_DIRECTORY = "./Audio/"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # UI START

        self.geometry("700x630")
        # self.resizable(False, False)
        self.title("YouTube Downloader")
        ctk.set_appearance_mode("System")

        # Image to display when no video thumbnail is available
        self.placeholder_image = ctk.CTkImage(
            Image.open("placeholder.png"), size=(350, 197))

        self.tabview = ctk.CTkTabview(
            self, segmented_button_selected_color="#ff0000", segmented_button_selected_hover_color="darkred")
        self.tabview.grid(row=0, column=0, sticky="nsew", **paddings)
        self.tabview.add("Videos")
        self.tabview.add("Playlists")

        # Frame for video info and progress indicators
        self.video_info_frame = ctk.CTkFrame(self.tabview.tab("Videos"))
        self.video_info_frame.grid(
            column=0, row=0, columnspan=2, **paddings, sticky="nsew")
        self.video_info_frame.columnconfigure(2, weight=1)

        self.thumbnail = ctk.CTkLabel(
            self.video_info_frame, text="", image=self.placeholder_image)
        self.thumbnail.grid(column=2, row=0, columnspan=2,
                            **paddings, sticky="nsew")

        self.pPercentage = ctk.CTkLabel(self.video_info_frame, text="")
        self.progressBar = ctk.CTkProgressBar(self.video_info_frame, width=300)
        self.progressBar.set(0)

        # Frame for link entry and download button
        self.input_frame = ctk.CTkFrame(self.tabview.tab("Videos"))
        self.input_frame.grid(column=0, row=2, columnspan=2,
                              sticky="nsew", **paddings)
        self.input_frame.columnconfigure(3, weight=1)
        self.input_frame.rowconfigure(1, weight=1)

        self.link = ctk.CTkEntry(self.input_frame, width=350, height=40,
                                 placeholder_text="Enter Youtube URL first!")
        self.link.grid(column=0, row=0, **paddings)
        self.link.configure(justify="center")

        self.option_menu = ctk.CTkOptionMenu(
            self.input_frame, height=40, values=("Resolutions:", "enter url!"), fg_color="#ff0000", button_color="#ff0000", button_hover_color="darkred", font=("Roboto", 15))
        self.option_menu.grid(column=1, row=0, **paddings)
        self.option_menu.configure(anchor="center")

        self.btn = ctk.CTkButton(self.input_frame, fg_color="#ff0000", hover_color="darkred", font=("Roboto", 20),
                                 text="Download", command=self.start_download, height=50)
        self.btn.grid(column=2, row=0, **paddings, sticky="e")

        # Frame for download list
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self.tabview.tab("Videos"), label_text="Downloaded:")
        self.scrollable_frame.grid(column=0, row=3, columnspan=2,
                                   sticky="nsew", **paddings)

    # FUNCTIONS

    def download_video(self):
        # Downloads the video and adds it to the download list afterwards

        # TODO: if higher resolutions are choosen i need to stitch them together with corresponding
        # audio since higher quality video (1080p upwards) comes without audio. i want to use ffmpeg here.

        vid_link = self.link.get()
        if self.is_yturl(vid_link):

            self.progressBar.grid(column=1, row=2, columnspan=2, pady=5)
            self.pPercentage.grid(column=1, row=3, columnspan=2)

            try:
                yt = YouTube(vid_link, on_progress_callback=self.on_progress)

                filtered_streams = yt.streams.filter(
                    res=self.option_menu.get())
                print(filtered_streams.first())

                if 'progressive="False"' in str(filtered_streams.first()):

                    filtered_streams.first().download(VIDEO_SAVE_DIRECTORY, filename="temp_vid.mp4")
                    yt.streams.filter(only_audio=True).first().download(
                        AUDIO_SAVE_DIRECTORY, filename="temp_aud.mp4")

                    video_clip = VideoFileClip(
                        VIDEO_SAVE_DIRECTORY + "temp_vid.mp4")
                    audio_clip = AudioFileClip(
                        AUDIO_SAVE_DIRECTORY + "temp_aud.mp4")
                    final_clip = video_clip.set_audio(audio_clip)
                    final_clip.write_videofile(
                        VIDEO_SAVE_DIRECTORY + yt.title + ".mp4")

                else:
                    filtered_streams.first().download(VIDEO_SAVE_DIRECTORY)

                # video = yt.streams.get_highest_resolution()

                final_image = self.get_thumbnail(
                    yt.thumbnail_url, 125, 70)

                last_downloaded_video = ctk.CTkLabel(self.scrollable_frame, font=("Roboto", 20), text="  " + shorten(
                    yt.title, width=30) + " by: " + shorten(yt.author, width=20), image=final_image, compound='left')
                last_downloaded_video.pack(**paddings)

                self.reset_after_download()

            except Exception as e:
                print(e)

    # Sets the current progress in the UI

    def on_progress(self, stream, chunk, bytes_remaining):
        # Sets the current progress in the UI

        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        per = str(int(percentage_of_completion))
        self.pPercentage.configure(text=per + "%")
        print(per)
        self.pPercentage.update()

        self.progressBar.set(float(percentage_of_completion / 100))

    def is_yturl(self, link):
        # Checks if link is a usable YT link

        id = self.parseYoutubeURL(link)
        checker_url = "https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v="
        video_url = checker_url + id
        request = requests.get(video_url)

        return request.status_code == 200

    def check_entry(self):
        # Checks entry box

        global vid_link
        global last_link
        vid_link = self.link.get()

        if vid_link != "" and vid_link != last_link:
            if self.is_yturl(vid_link):
                self.link.configure(border_color="green")
                print("is url")
                yt = YouTube(vid_link)
                threading.Thread(target=self.insert_video_info(yt)).start()

            else:
                print("not url")
                self.link.configure(border_color="red")
                self.thumbnail.configure(text="", image=self.placeholder_image)
                self.option_menu.configure(values="")
                self.option_menu.configure(
                    values=("Resolutions:", "enter url!"))
        last_link = vid_link
        self.after(2000, self.check_entry)

    def start_download(self):
        # Starts the download thread if not already started

        thread_names = [t.name for t in threading.enumerate()]

        if "download_thread" not in thread_names:
            download_thread = threading.Thread(
                target=self.download_video, name="download_thread")
            download_thread.start()

    def reset_after_download(self):
        # Resets the state after download

        self.thumbnail.configure(text="", image=self.placeholder_image)
        self.progressBar.set(0)
        self.progressBar.grid_forget()
        self.pPercentage.configure(text="")
        self.pPercentage.grid_forget()
        self.link.delete(0, ctk.END)
        self.link.configure(border_color="grey")
        self.option_menu.configure(values=("Resolutions:", "enter url!"))

    def get_thumbnail(self, link, x, y):
        # Gets the thumbnail out of a link and returns it as a CTkImage

        u = urllib.request.urlopen(link)
        raw_data = u.read()
        u.close()

        im = Image.open(BytesIO(raw_data))
        final_image = ctk.CTkImage(dark_image=im, size=(x, y))

        return final_image

    def check_resolutions(self, streams):
        self.option_menu.configure(values="")
        temp_list = []

        for i in resolutions:
            if i in str(streams):
                temp_list.append(i)

        self.option_menu.configure(values=temp_list)
        self.option_menu.set(temp_list[0])

    def insert_video_info(self, yt):
        try:
            final_image = self.get_thumbnail(
                yt.thumbnail_url, 350, 197)

            self.thumbnail.configure(image=final_image, font=("Roboto", 20), compound='top',
                                     text=shorten(yt.title, width=50) + " by: " + shorten(yt.author, width=15) + "\nduration: " +
                                     strftime("%H:%M:%S", gmtime(yt.length)) + " | views: " + f'{yt.views:,d}')
            self.thumbnail.image = final_image

            self.check_resolutions(yt.streams)
        except Exception as e:
            print(e)

    def parseYoutubeURL(self, url: str) -> str:
        data = re.findall(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if data:
            return data[0]
        return ""


if __name__ == "__main__":
    app = App()
    # run this function again 2,000 ms from now
    app.after(2000, app.check_entry)
    app.mainloop()
