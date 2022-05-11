"""
Handles YouTube links by extracting the necessary information to properly
store information in the database.
"""
import os
import pytube
import wave
import struct
from pydub import AudioSegment
import sys
sys.path.append("/usr/local/lib/python3.9/dist-packages")
import librosa

MAX_LENGTH = 10 # maximum supported video length in minutes

# Given the name of the audio file, return the absolute path of the audio file
# regardless of the current working directory
def get_audio_path(audio_file):
    wd = os.path.abspath(os.getcwd())
    path = wd.split("/nicer-rack",1)[0] + "/nicer-rack/audio_files/" + str(audio_file)
    return path

def download_link_data(link):
    """Extracts the title, duration in seconds, stripped YouTube link, 
    and thumbnail url, and downloads audio from the link

    Arguments:
        link: String YouTube link, query argument only
    Returns: tuple of (String title, Float duration, String link, String thumbnail, String filepath). 
    None if link not accessible or does not exist"""
    # Pytube requires link to start with youtube in url
    yt_link = "youtube.com/watch?v=" + link
    try:
        vid = pytube.YouTube(yt_link)
        vid.check_availability()
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
    audio_file = audio.download(output_path=get_audio_path(""), filename=link)

    #Save the file as .mp3, define relative filepath to return
    base, ext = os.path.splitext(audio_file)
    abs_filepath = base + '.mp3'
    os.rename(audio_file, abs_filepath)
    filepath = get_audio_path(link) + ".mp3"

    return (title, duration, link, filepath, thumbnail)

def convert_mp3_to_wav(path):
    """Given an absolute path to a .mp3 audio file, converts the audio to
    a numpy array of audio samples
    Arguments:
        path: String relative path to .mp3 file
    Returns: List of sampled audio 16 bits per sample
    """
    y, sr = librosa.load(path, sr=44100)
    y = y * (2**15)
    y = y.astype(int)
    return y
