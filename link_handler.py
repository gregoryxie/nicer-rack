"""
Handles YouTube links by extracting the necessary information to properly
store information in the database.
"""
import os
import pytube
import wave
import struct
from pydub import AudioSegment

MAX_LENGTH = 10 # maximum supported video length in minutes

def extract_link_data(link):
    """Extracts the title, duration in seconds, stripped YouTube link, 
    and thumbnail url, and downloads audio from link. 

    Arguments:
        link: String YouTube link, query argument only
    Returns: tuple of (String title, Float duration, String link, String thumbnail, String filepath). 
    None if link not accessible or does not exist"""
    # Clean YouTube link and access video from link
    # yt_link = clean_link(link)
    yt_link = "youtube.com/watch?v=" + link
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
    audio_file = audio.download(output_path="../../audio_files/", filename=filename)

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

def convert_mp3_to_wav(path):
    """Given a relative path to a .mp3 audio file, converts the audio to .wav
    format. Must export .mp3 to .wav file first, before sampling .wav. Then .wav
    file can be deleted from directory.
    Arguments:
        path: String relative path to .mp3 file
    Returns: List of sampled audio from .wav file at 16 bits per sample
    """
    # Extract the filename of the mp3 from the path
    filename = path.split("/audio_files/",1)[1]
    filename = filename.split(".mp3",1)[0]
    filename_wav = "{}.wav".format(filename)
    samples = []

    # In some cases the dependency ffmpeg will misread a .mp3 file, and requires a .mp4 container
    # https://stackoverflow.com/questions/70660431/couldntdecodeerror-decoding-failed-ffmpeg-returned-error-code-69
    try:
        sound = AudioSegment.from_file(path, "mp3")
    except:
        sound = AudioSegment.from_file(path, format="mp4")

    # Export the sound into a .wav file in the root folder to be read
    sound.export(filename_wav, format="wav")

    # Use wave to read .wav file and extract samples to array
    if os.path.exists(filename_wav):
        # Read all of the frames from the .wav file and place into a bytestring
        audio_wav = wave.open(filename_wav, 'rb')
        nframes = audio_wav.getnframes()
        bytestring = audio_wav.readframes(audio_wav.getnframes())

        # By default, the .wav file is read from at 32 bits at a time, so
        # unpack into 2 16 bit integers and add to samples both integers
        for frame in range(nframes):
            ind = 4*frame
            samples += list(struct.unpack("<hh", bytestring[ind:ind+4]))

        # Close the connection to the .wav file
        audio_wav.close()

        # Delete the .wav file as no longer needed
        os.remove(filename_wav)

    # Return the list of 2-byte integer samples of the audio for future processing/streaming
    return samples
