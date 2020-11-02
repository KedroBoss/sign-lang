import getopt
import sys
from enum import IntEnum, auto
import ffmpy
import os
import re
import requests
import csv
from bs4 import BeautifulSoup
IMGS_DIR = "source/hiragana_files"
SOURCE = "source/"
CSV_FILE_NAME = "hiragana.csv"
POSTFIX = "/master.m3u8"
VIDEO_DIR = "source/video/"


def get_link_to_player(original_page_link):
    print("Getting link to the player page")
    req = requests.get(original_page_link)
    # with open(file) as f:
    soup = BeautifulSoup(req.text, "html.parser")
    # Get the link to player page
    modal = soup.find(id="basic-modal").a["href"]
    return modal, soup


def get_name_from_original_page(original_page_data: BeautifulSoup):
    return original_page_data.find("div", class_="hgroup").h2.text


def get_link_to_video_from_player_page(player_page):
    print("Getting link to the video from the player page")

    req = requests.get("https://www2.nhk.or.jp/signlanguage/" + player_page)
    soup = BeautifulSoup(req.content, "html.parser")

    # Find the link to the video on the player page
    link_raw = soup.find("form").find("input")["value"]
    return link_raw


def get_video_from_link_to_video(link_to_video, custom_name=""):
    print("Getting video from the link to the video")
    video_name = custom_name
    if custom_name == "":
        video_name = link_to_video.split("/")[-1][:-4]

    req = requests.get(link_to_video + POSTFIX, allow_redirects=True)

    open(VIDEO_DIR + video_name + ".mp4", "wb").write(req.content)

    return video_name


def download_video(link):
    player_page, original_page = get_link_to_player(link)
    name_on_page = get_name_from_original_page(original_page)
    video_link = get_link_to_video_from_player_page(player_page)
    video_name = get_video_from_link_to_video(
        video_link, custom_name=name_on_page)
    print("Download is completed")
    return name_on_page


def make_CSV(csv_file_name, text, image_link, video_name=None):
    with open(csv_file_name, "w", newline='') as file:
        writer = csv.writer(file, delimiter=",")
        data = []
        if video_name == None:
            data = [text, "<img src='{}' />".format(image_link)]
        else:
            data = [
                text, "<img src='{}' />".format(image_link), "<img src='{}' />".format(video_name)]
        writer.writerow(data)


class Convertable(IntEnum):
    GIF = auto()
    MP4 = auto()


def convert_folder(folder, convert_to: Convertable, convert_from: Convertable):
    with os.scandir(folder) as videos:
        for video in videos:
            convert_one_video(folder, video.name,
                              convert_to=convert_to, convert_from=convert_from)


def convert_one_video(folder, video_name, convert_to: Convertable, convert_from: Convertable, new_name=""):
    print("Converting {} of type {} in the {} to the {} with the new name of {}".format(
        video_name, str(convert_from), folder, str(convert_to), new_name))
    name_without_type = video_name.split(".")[0]
    if convert_to == Convertable.GIF:
        convert_to = "gif"
    elif convert_to == Convertable.MP4:
        convert_to = "mp4"

    if convert_from == Convertable.GIF:
        convert_from = "gif"
    elif convert_from == Convertable.MP4:
        convert_from = "mp4"

    if new_name == "":
        new_name = name_without_type
    ff = ffmpy.FFmpeg(
        inputs={
            folder + video_name + "." + convert_from: '-protocol_whitelist file,http,https,tcp,tls,crypto'},
        outputs={folder + new_name + "." + convert_to: '-vf scale=320:-1'}
    )
    ff.run()


print('Number of args is ', len(sys.argv))
print('List is ', str(sys.argv))


def main(argv):
    try:
        args, vals = getopt.getopt(argv, "n:i:", ["name=", "input="])
    except getopt.error as err:
        print(str(err))
        sys.exit(2)

    name = ""
    for cur_arg, cur_val in args:
        if cur_arg in ("-n", "--name"):
            print("Name is ", cur_val)
            name = cur_val
        elif cur_arg in ("-i", "--input"):
            print("Input is ", cur_val)
            video_name = download_video(cur_val)
            convert_one_video(VIDEO_DIR, video_name,
                              convert_to=Convertable.GIF, convert_from=Convertable.MP4, new_name=name)


if __name__ == "__main__":
    print("Start")
    main(sys.argv[1:])
    print("COMPLETE!!!")
