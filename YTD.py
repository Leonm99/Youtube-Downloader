from pytube import YouTube
from PIL import Image
from io import BytesIO
from textwrap import shorten
from time import strftime
from time import gmtime
from os import remove
import customtkinter as ctk
import urllib.request
import threading
import requests
import re
import ffmpeg

# ---------------- Temporary Patch -------------------
# lower pytube download chunk size so the progressbar updates more frequent
# pytube.request.default_range_size = 2097152
# Accessing title is currently failing due to a change in the pytube library
# https://github.com/hayabhay/whisper-ui/issues/43
# This is currently a temporary patch to fix the issue
# https://github.com/pytube/pytube/commit/c0d1aca42c4106e77ab4f8a0600737ea2ad27a96
# pytube.innertube._default_clients['ANDROID'] = pytube.innertube._default_clients['WEB']

vid_link = " "
last_link = " "
resolutions = ("2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p")
paddings = {"padx": 5, "pady": 5}
sticky = {"sticky": "nsew"}
VIDEO_SAVE_DIRECTORY = "./Videos/"
AUDIO_SAVE_DIRECTORY = "./Audio/"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ---------------- UI -------------------

        self.geometry("700x630")
        self.minsize(width=700, height=630)
        # self.resizable(False, False)
        self.title("YouTube Downloader")
        ctk.set_appearance_mode("System")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Image to display when no video thumbnail is available
        self.placeholder_image = ctk.CTkImage(
            Image.open("placeholder.png"), size=(350, 197)
        )

        # Frame for video info and progress indicators
        self.video_info_frame = ctk.CTkFrame(self, width=350, height=197)
        self.video_info_frame.columnconfigure(2, weight=1)
        self.video_info_frame.grid(column=0, row=0, **paddings, **sticky)
        self.console = ctk.CTkTextbox(
            self,
            wrap="word",
            state="disabled",
            font=("Lucida Console", 12),
        )
        self.console.grid(column=1, row=0, **paddings, **sticky)

        # Label that holds thumbnail and video info
        self.thumbnail = ctk.CTkLabel(
            self.video_info_frame, text="", image=self.placeholder_image
        )
        self.thumbnail.grid(column=2, row=0, columnspan=2, **paddings, **sticky)

        # Label that shows download percentage
        self.pPercentage = ctk.CTkLabel(self.video_info_frame, text="")
        # Progressbar
        self.progressBar = ctk.CTkProgressBar(self.video_info_frame, width=300)
        self.progressBar.set(0)

        # Frame for link entry and download button
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(column=0, row=2, columnspan=2, **paddings, **sticky)
        self.input_frame.columnconfigure(2, weight=1)
        self.input_frame.rowconfigure(0, weight=1)

        # Button that starts download
        self.btn = ctk.CTkButton(
            self.input_frame,
            fg_color="#ff0000",
            hover_color="darkred",
            font=("Roboto", 20),
            text="Download",
            command=self.download_button_pressed,
            height=50,
        )
        self.btn.grid(column=0, row=0, **paddings, **sticky)

        # Dropdown to choose resolution of video
        self.option_menu = ctk.CTkOptionMenu(
            self.input_frame,
            height=40,
            values=("Resolutions:", "enter url!"),
            fg_color="#ff0000",
            button_color="#ff0000",
            button_hover_color="darkred",
            font=("Roboto", 15),
        )
        self.option_menu.grid(column=1, row=0, **paddings)
        self.option_menu.configure(anchor="center")

        # Entry box for youtube link
        self.link = ctk.CTkEntry(
            self.input_frame,
            width=350,
            height=40,
            placeholder_text="Enter Youtube URL first!",
        )
        self.link.grid(column=2, row=0, **paddings, **sticky)
        self.link.configure(justify="center")

        # Frame for download list
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self, label_text="Last downloaded:"
        )
        self.scrollable_frame.grid(column=0, row=3, columnspan=2, **paddings, **sticky)

    # ---------------- FUNCTIONS -------------------

    def check_entry(self):  # sourcery skip: extract-method
        # checks the entry box for valid youtube link, when found

        global vid_link
        global last_link
        vid_link = self.link.get()

        if vid_link not in ["", last_link]:
            if self.is_yturl(vid_link):
                self.link.configure(border_color="green")
                self.write_info("Link is valid. ✓")

                print("is url")

                yt = YouTube(vid_link)

                threading.Thread(
                    target=self.check_resolutions,
                    args=(yt.streams,),
                    name="check_resolutions_thread",
                ).start()

                threading.Thread(
                    target=self.insert_video_info, args=(yt,), name="insert_info_thread"
                ).start()

            else:
                self.write_info("Link is invalid. ❌")
                print("not url")
                self.link.configure(border_color="red")
                self.thumbnail.configure(text="", image=self.placeholder_image)
                self.option_menu.configure(values="")
                self.option_menu.configure(values=("Resolutions:", "enter url!"))

        last_link = vid_link

        self.after(1000, self.check_entry)

    def is_yturl(self, link):
        # Checks if link is a usable YT link
        try:
            url_id = self.parseYoutubeURL(link)
            checker_url = (
                "https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v="
            )
            video_url = checker_url + url_id
            request = requests.get(video_url)
        except Exception as e:
            print(e)

        return request.status_code == 200

    def parseYoutubeURL(self, url: str) -> str:
        if data := re.findall(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url):
            return data[0]
        return ""

    def get_thumbnail(self, link, x, y):
        # Gets the thumbnail out of a link and returns it as a CTkImage
        try:
            u = urllib.request.urlopen(link)
            raw_data = u.read()
            u.close()

            im = Image.open(BytesIO(raw_data))
            return ctk.CTkImage(dark_image=im, size=(x, y))
        except Exception as e:
            print(e)
            self.write_info(str(e))

    def check_resolutions(self, streams):
        self.option_menu.configure(values="")
        temp_list = [
            f"{i} - {str(round(streams.filter(res=i).first().filesize / 1024 / 1024, 1))}MB"
            for i in resolutions
            if i in str(streams)
        ]
        self.option_menu.configure(values=temp_list)
        self.option_menu.set(temp_list[0])

    def insert_video_info(self, yt):
        try:
            final_image = self.get_thumbnail(yt.thumbnail_url, 350, 197)

            self.thumbnail.configure(
                image=final_image,
                font=("Roboto", 15),
                compound="top",
                text=(
                    (
                        (
                            f"{shorten(yt.title, width=45)} by: {shorten(yt.author, width=15)}"
                            + "\nduration: "
                            + strftime("%H:%M:%S", gmtime(yt.length))
                        )
                        + " | views: "
                    )
                    + f"{yt.views:,d}"
                ),
            )

            self.thumbnail.image = final_image
        except Exception as e:
            print(e)

    def download_button_pressed(self):
        # Starts the download thread if not already started
        thread_names = [t.name for t in threading.enumerate()]
        if "download_thread" not in thread_names:
            self.write_info("Starting download...")
            download_thread = threading.Thread(
                target=self.download_video, name="download_thread"
            )
            download_thread.start()

    def download_video(self):  # sourcery skip: extract-method
        # Downloads the video and adds it to the download list afterwards

        vid_link = self.link.get()

        if self.is_yturl(vid_link):
            self.progressBar.grid(column=1, row=2, columnspan=2, pady=5)
            self.pPercentage.grid(column=1, row=3, columnspan=2)

            yt = YouTube(vid_link, on_progress_callback=self.on_progress)
            filtered_streams = yt.streams.filter(
                res=self.option_menu.get().split(" ")[0]
            )

            try:
                if 'progressive="False"' in str(filtered_streams.first()):
                    self.download_and_connect(filtered_streams, yt)
                else:
                    filtered_streams.first().download(VIDEO_SAVE_DIRECTORY)
            except Exception as e:
                print(e)

        self.write_info("Download completed.", True)

        self.log_last_download(yt)

        self.reset_after_download()

    def download_and_connect(self, filtered_streams, yt):
        self.write_info(
            "Progressive stream not available, downloading video and audio seperately and combining them..."
        )

        self.write_info("Downloading video...")
        t1 = threading.Thread(
            target=filtered_streams.first().download(
                VIDEO_SAVE_DIRECTORY, filename="temp_vid.mp4"
            ),
            name="download_video_thread",
        )

        self.write_info("Downloading audio...")
        t2 = threading.Thread(
            target=yt.streams.get_audio_only().download(
                AUDIO_SAVE_DIRECTORY, filename="temp_aud.mp4"
            ),
            name="download_audio_thread",
        )

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        video_stream = ffmpeg.input(f"{VIDEO_SAVE_DIRECTORY}temp_vid.mp4")
        audio_stream = ffmpeg.input(f"{AUDIO_SAVE_DIRECTORY}temp_aud.mp4")

        self.write_info("Combining video and audio using ffmpeg...")
        ffmpeg.output(
            audio_stream, video_stream, VIDEO_SAVE_DIRECTORY + yt.title + ".mp4"
        ).run(overwrite_output=True)

        remove(f"{VIDEO_SAVE_DIRECTORY}temp_vid.mp4")
        remove(f"{AUDIO_SAVE_DIRECTORY}temp_aud.mp4")

    def on_progress(self, stream, chunk, bytes_remaining):
        # Sets the current progress in the UI

        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        per = str(int(percentage_of_completion))
        self.pPercentage.configure(text=f"{per}%")
        print(per)
        self.pPercentage.update()

        self.progressBar.set(float(percentage_of_completion / 100))

    def log_last_download(self, yt):
        final_image = self.get_thumbnail(yt.thumbnail_url, 125, 70)

        last_downloaded_video = ctk.CTkLabel(
            self.scrollable_frame,
            font=("Roboto", 20),
            text=f"  {shorten(yt.title, width=30)} by: {shorten(yt.author, width=20)}",
            image=final_image,
            compound="left",
        )
        last_downloaded_video.pack(**paddings)

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
        self.option_menu.set("Resolutions:")

    def write_info(self, string, clear=False):
        self.console.configure(state="normal")
        if clear:
            self.console.delete("0.0", "end")
        self.console.insert(ctk.INSERT, string + "\n" + "\n")
        self.console.configure(state="disabled")


if __name__ == "__main__":
    app = App()
    # run this function again 2,000 ms from now
    app.after(2000, app.check_entry)
    app.mainloop()
