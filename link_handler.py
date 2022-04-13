"""
Handles YouTube links by extracting the necessary information to properly
store information in the database.
"""
import os
import pytube

MAX_LENGTH = 10 # maximum supported video length in minutes

def extract_link_data(link):
    """Extracts the title, duration in seconds, stripped YouTube link, 
    and thumbnail url, and downloads audio from link. 

    Arguments:
        link: String YouTube link
    Returns: tuple of (String title, Float duration, String link, String thumbnail, String filepath). 
    None if link not accessible or does not exist"""
    # Clean YouTube link and access video from link
    yt_link = clean_link(link)
    try:
        vid = pytube.YouTube(yt_link)
        vid.check_availability()

        # Extract filename of the mp3 as the url query argument,
        # as unique for each video, unlike titles
        filename = yt_link.split("watch?v=",1)[1]
    except:
        return None

    title = vid.title
    duration = int(vid.length)
    thumbnail = vid.thumbnail_url
    # Do not download if duration of video is too long
    if duration > 60 * MAX_LENGTH:
        return None

    # Extract only audio from the video, and download to audio_files directory
    audio = vid.streams.filter(only_audio=True).first()
    audio_file = audio.download(output_path="./audio_files/", filename=filename)

    #Save the file as .mp3, define relative filepath to return
    base, ext = os.path.splitext(audio_file)
    abs_filepath = base + '.mp3'
    os.rename(audio_file, abs_filepath)
    filepath = "./audio_files/{}.mp3".format(filename)

    return (title, duration, yt_link, filepath, thumbnail)

def clean_link(link):
    """Cleans the YouTube link into proper format, starting at 'youtube' to 
    the first url argument.
    Arguments:
        link: String YouTube link
    Returns: 
    """
    # Cut off all url query arguments past the first, as only link to video needed
    link = link.strip().split("&")[0]

    # Cut off the head of the link, so that link starts with youtube
    link_split = link.split("www.",1)
    if len(link_split) == 2:
        return link_split[1]
    return link
