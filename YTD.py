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
resolutions = ("2160p", "1440p", "1080p", "720p",
               "480p", "360p", "240p", "144p")
paddings = {'padx': 5, 'pady': 5}

VIDEO_SAVE_DIRECTORY = "./Videos"
AUDIO_SAVE_DIRECTORY = "./Audio"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # UI START

        self.geometry("720x570")
        # self.resizable(False, False)
        self.title("YouTube Downloader")
        ctk.set_appearance_mode("System")

        # Image to display when no video thumbnail is available
        self.placeholder_image = ctk.CTkImage(
            Image.open("placeholder.png"), size=(350, 197))

        self.tabview = ctk.CTkTabview(
            self, segmented_button_selected_color="red", segmented_button_selected_hover_color="darkred")
        self.tabview.grid(row=1, column=0, **paddings,
                          sticky="nsew")
        self.tabview.add("Videos")
        self.tabview.add("Playlists")

        # Frame for video info and progress indicators
        self.video_info_frame = ctk.CTkFrame(self.tabview.tab("Videos"))
        self.video_info_frame.grid(
            column=0, row=0, **paddings, sticky="nsew")
        self.video_info_frame.columnconfigure(2, weight=1)

        self.thumbnail = ctk.CTkLabel(
            self.video_info_frame, text="", image=self.placeholder_image)
        self.thumbnail.grid(column=2, row=0, columnspan=2,
                            **paddings, sticky="nsew")

        self.pPercentage = ctk.CTkLabel(self.video_info_frame, text="")
        self.progressBar = ctk.CTkProgressBar(self.video_info_frame, width=300)
        self.progressBar.set(0)

        self.video_settings_frame = ctk.CTkFrame(
            self.tabview.tab("Videos"))
        self.video_settings_frame.grid(
            column=1, row=0, sticky="nsew", **paddings)
        self.video_settings_frame.columnconfigure(0, weight=1)

        self.option_menu = ctk.CTkOptionMenu(
            self.video_settings_frame, values=resolutions)
        self.option_menu.grid(column=0, row=0, **paddings, sticky="nsew")
        self.option_menu.configure(anchor="center")

        # Frame for link entry and download button
        self.input_frame = ctk.CTkFrame(self.tabview.tab("Videos"))
        self.input_frame.grid(column=0, row=2, columnspan=2,
                              sticky="nsew", **paddings)
        self.input_frame.columnconfigure(3, weight=1)
        self.input_frame.rowconfigure(1, weight=1)

        self.link = ctk.CTkEntry(self.input_frame, width=500, height=40,
                                 placeholder_text="Youtube URL")
        self.link.grid(column=0, row=0, **paddings)
        self.link.configure(justify="center")

        self.btn = ctk.CTkButton(self.input_frame, fg_color="red", hover_color="darkred", font=("Roboto", 20),
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
        if self.is_yturl():

            self.progressBar.grid(column=1, row=2, columnspan=2, pady=5)
            self.pPercentage.grid(column=1, row=3, columnspan=2)

            try:
                yt = YouTube(vid_link, on_progress_callback=self.on_progress)

                filtered_streams = yt.streams.filter(
                    res=self.option_menu.get())
                print(filtered_streams)
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

    def is_yturl(self):
        # Checks if link is a usable YT link (this needs some refinement!)

        # TODO: check what resolutions are available and add them to a list, set this list as
        # option menu choices and then pack it into the frame

        vid_link = self.link.get()

        if "https://www.youtube.com/watch?v=" in vid_link and len(vid_link) > 42:

            print("is url")

            yt = YouTube(vid_link)

            try:

                final_image = self.get_thumbnail(
                    yt.thumbnail_url, 350, 197)

                self.thumbnail.configure(image=final_image, font=("Roboto", 20), compound='top',
                                         text=shorten(yt.title, width=30) + " by: " + shorten(yt.author, width=20) + "\nduration: " +
                                         strftime("%H:%M:%S", gmtime(yt.length)) + " | views: " + f'{yt.views:,d}')
                self.thumbnail.image = final_image

            except Exception as e:
                print(e)

            return True

        else:
            print("not url")
            self.thumbnail.configure(text="", image=self.placeholder_image)
            return False

    def check_entry(self):
        # Checks entry box

        global vid_link
        global last_link
        vid_link = self.link.get()

        if vid_link != last_link:
            threading.Thread(target=self.is_yturl).start()

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

    def get_thumbnail(self, link, x, y):
        # Gets the thumbnail out of a link and returns it as a CTkImage

        u = urllib.request.urlopen(link)
        raw_data = u.read()
        u.close()

        im = Image.open(BytesIO(raw_data))
        final_image = ctk.CTkImage(dark_image=im, size=(x, y))

        return final_image


if __name__ == "__main__":
    app = App()
    # run this function again 2,000 ms from now
    app.after(2000, app.check_entry)
    app.mainloop()
