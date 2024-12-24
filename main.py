import streamlit as st
import re
import whisper
import google.generativeai as genai
import os
import yt_dlp
import tempfile

def load_gemini_api_key():
    try:
        with open("license.txt", "r") as f:
            api_key = f.readline().strip()
        return api_key
    except FileNotFoundError:
        st.error("license.txt file not found. Please ensure it exists in the same directory as your script.")
        return None
    except Exception as e:
       st.error(f"Error reading API key from license.txt: {e}")
       return None

gemini_api_key = load_gemini_api_key()

if gemini_api_key:
  genai.configure(api_key=gemini_api_key)
  model = genai.GenerativeModel("gemini-1.5-flash")
else:
  st.stop() #stop the app if API Key does not exist

def download_audio(url, tmpdir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '%(id)s.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        audio_file = ydl.prepare_filename(info_dict)
        ydl.download(url)
    return audio_file

def is_islamic_video(url, transcript):
        keywords = ["allah", "muhammad", "islam", "muslim", "quran", "hadith", "ramadan", "prayer", "mosque", "jihad", "zakat", "hijab"]
        text_lower = " ".join([segment['text'] for segment in transcript]).lower()
        for keyword in keywords:
            if keyword in text_lower:
                return True
        return False

def transcribe_video(url):
        device = "cpu"
        model = whisper.load_model("base", device=device)
        st.info("Transcription started...")
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = download_audio(url, tmpdir)
            result = model.transcribe(audio_file)
            os.remove(audio_file)
            st.success("Transcription completed!")
            return result["segments"]

def generate_response(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
      st.error(f"Error when doing query to gemini {e}")
      return None

st.title("Islamic YouTube Chat")

youtube_url = st.text_input("Enter YouTube Video URL")

if youtube_url:
    if 'transcript' not in st.session_state or st.session_state.get('video_url') != youtube_url:
      with st.spinner("Downloading and transcribing"):
          transcript = transcribe_video(youtube_url)
          st.session_state['transcript'] = transcript
          st.session_state['video_url'] = youtube_url
    else:
        transcript = st.session_state['transcript']

    if is_islamic_video(youtube_url, transcript):
        st.success("This video is related to Islamic topics.")

        if st.checkbox("Show full transcript"):
            for segment in transcript:
              st.write(f"{segment['start']} - {segment['end']}: {segment['text']}")
        else:
             st.write("Transcript is collapsed. Check the checkbox above to show the full transcript")

        chat_input = st.text_input("Enter your question")
        if chat_input:
           prompt = f"Based on this transcript: {transcript} \nAnswer this question: {chat_input}"
           with st.spinner('Generating response...'):
              response = generate_response(prompt + " jawab pakai bahasa indonesia")
              if response:
                  st.write(f"**Answer**: {response}")

    else:
        st.error("This video does not appear to be related to Islamic topics.")