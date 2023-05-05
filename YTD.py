from pytube import YouTube
import pytube.request
import customtkinter as ctk
import tkinter

# https://www.youtube.com/watch?v=Yw6u6YkTgQ4 short
# https://www.youtube.com/watch?v=PJ0i8hkeabc middle
# 9MB chunk size       1048576  1MB chunk size
pytube.request.default_range_size = 2097152


def startDownload():
    try:
        ytlink = link.get()
        yt = YouTube(ytlink, on_progress_callback=on_progress)
        video = yt.streams.get_highest_resolution()

        # title.configure(text=yt.title, text_color="white")
        finishLabel.configure(text="")
        video.download()
        finishLabel.configure(text="Downloaded!")
    except EOFError as err:
        print(err)
        finishLabel.configure(text="Error", text_color="red")


def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    per = str(int(percentage_of_completion))
    pPercentage.configure(text=per + "%")
    print(per)
    pPercentage.update()

    progressBar.set(float(percentage_of_completion / 100))


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.geometry("720x480")
app.title("YouTube Downloader")


title = ctk.CTkLabel(app, text="Insert YouTube link")
title.pack(padx=10, pady=10)

url_var = tkinter.StringVar()
link = ctk.CTkEntry(app, width=350, height=40, textvariable=url_var)
link.pack(padx=10, pady=10)

finishLabel = ctk.CTkLabel(app, text="")
finishLabel.pack()

pPercentage = ctk.CTkLabel(app, text="0%")
pPercentage.pack()

progressBar = ctk.CTkProgressBar(app, width=400)
progressBar.set(0)
progressBar.pack(padx=10, pady=10)

btn = ctk.CTkButton(app, text="Download", command=startDownload)
btn.pack(padx=10, pady=10)


app.mainloop()
