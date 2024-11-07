import streamlit as st
import yt_dlp
import os
import subprocess

# Function to get available formats
def get_formats(url):
    ydl_opts = {
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        formats = info_dict.get('formats', [])
        video_formats = [f for f in formats if f.get('vcodec') != 'none']
        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
        return video_formats, audio_formats
    
def download_selected_format(url, format_id, download_type):
    if download_type == 'Audio':
        # For audio, convert to MP3 with bitrate 320k
        ydl_opts = {
            'format': format_id,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    elif download_type == 'Video':
        ydl_opts = {
            'format': format_id,
            'outtmpl': 'downloads/%(title)s.%(ext)s',
        }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url)
        filename = ydl.prepare_filename(info_dict)
        return filename
    
# Function to merge video and audio with audio conversion to AAC at 256 kbps
def merge_video_and_audio(video_filepath, audio_filepath):
    output_filename = os.path.splitext(video_filepath)[0] + "_merged.mp4"
    command = [
        'ffmpeg', '-i', video_filepath, '-i', audio_filepath,
        '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', output_filename
    ]
    subprocess.run(command, check=True)
    return output_filename

# Function to delete files
def delete_files(*filepaths):
    for filepath in filepaths:
        if os.path.exists(filepath):
            os.remove(filepath)

# Streamlit App
st.title('YouTube MP4 and MP3 Downloader')

url = st.text_input('Enter YouTube URL:')
if url:
    video_formats, audio_formats = get_formats(url)

    # Ask user what they want to download
    download_type = st.radio('Download:', ('Video', 'Audio'))

    if download_type == 'Video':
        st.subheader('Select Video Quality')
        video_format_options = [
            f"{f.get('format_id', '')} - {f.get('format_note', '')} - {(f.get('filesize', 0) or 0) / (1024 * 1024):.2f} MB"
            for f in video_formats if 'filesize' in f and 'format_id' in f and 'format_note' in f]
        selected_video_format = st.selectbox('Video Formats', video_format_options, key='video_format')
        selected_video_format_id = selected_video_format.split(' - ')[0]

        # For video, default to highest available audio quality
        audio_format_options = [
            f"{f.get('format_id', '')} - {f.get('format_note', '')} - {(f.get('filesize', 0) or 0) / (1024 * 1024):.2f} MB"
            for f in audio_formats if 'filesize' in f and 'format_id' in f and 'format_note' in f]
        selected_audio_format_id = audio_formats[0]['format_id'] if audio_formats else None

    elif download_type == 'Audio':
        st.subheader('Select Audio Quality')
        audio_format_options = [
            f"{f.get('format_id', '')} - {f.get('format_note', '')} - {(f.get('filesize', 0) or 0) / (1024 * 1024):.2f} MB"
            for f in audio_formats if 'filesize' in f and 'format_id' in f and 'format_note' in f]
        selected_audio_format = st.selectbox('Audio Formats', audio_format_options, key='audio_format')
        selected_audio_format_id = selected_audio_format.split(' - ')[0]

if st.button('Download'):
    if download_type == 'Video':
        try:
            video_filepath = download_selected_format(url, selected_video_format_id, 'Video')
            if selected_audio_format_id:
                audio_filepath = download_selected_format(url, selected_audio_format_id, 'Video')
                merged_filepath = merge_video_and_audio(video_filepath, audio_filepath)
                st.success('Video Downloaded Sucessfully!')
                st.write(f'Merged file path: {merged_filepath}')
                delete_files(video_filepath, audio_filepath)
                
                # Enable download of merged file
                with open(merged_filepath, 'rb') as f:
                    st.download_button(
                        label="Download Merged Video",
                        data=f,
                        file_name=os.path.basename(merged_filepath),
                        mime="video/mp4"
                    )
            else:
                st.error('No audio format available for this video.')
        except Exception as e:
            st.error(f'Error: {str(e)}')
    elif download_type == 'Audio':
        try:
            audio_filepath = download_selected_format(url, selected_audio_format_id, 'Audio')
            st.success('Audio downloaded successfully!')
            
            # Enable download of audio file
            with open(audio_filepath, 'rb') as f:
                st.download_button(
                    label="Download Audio",
                    data=f,
                    file_name=os.path.basename(audio_filepath),
                    mime="audio/mpeg"
                )

        except Exception as e:
            st.error(f'Error: {str(e)}')
