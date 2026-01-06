# AssemblyAI AI Voice Bot
# MIT License (see LICENSE file)
#
# Usage: Set ELEVENLABS_API_KEY as an environment variable before running.
# Example:
#   $env:ELEVENLABS_API_KEY="your_actual_api_key"
#   python app.py

import speech_recognition as sr
from elevenlabs import generate, stream
import requests
import re
import os
import subprocess

class AI_Assistant:
    def __init__(self):
        self.gemini_api_key = "AIzaSyCRG_Qt4kdUhYHKDST7dfdv7Chj_cqW3nU"  # <-- Replace with your Gemini API key
        self.elevenlabs_api_key = "sk_92cee6ff667f6c1e653a39415c1917a1420dea684c01ebc7"
        self.full_transcript = [
            {"role": "system", "content": "You are a receptionist at a dental clinic. Be resourceful and efficient."},
        ]
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False

    def start_transcription(self):
        print("\nReal-time transcription started. Speak into your microphone.")
        print("Say 'exit', 'quit', or 'stop' to end the assistant.")
        self.listening = True
        while self.listening:
            with self.microphone as source:
                print("Listening...")
                audio = self.recognizer.listen(source)
            try:
                transcript = self.recognizer.recognize_google(audio)
                print(f"Patient: {transcript}")
                if transcript.strip().lower() in ["exit", "quit", "stop"]:
                    print("Exiting assistant. Goodbye!")
                    self.stop_transcription()
                    break
                self.generate_ai_response(transcript)
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}")

    def stop_transcription(self):
        self.listening = False

    def get_first_gemini_model(self):
        url = "https://generativelanguage.googleapis.com/v1/models"
        headers = {"x-goog-api-key": self.gemini_api_key}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            print("[Gemini API available models]", result)
            for model in result.get("models", []):
                if "generateContent" in model.get("supportedGenerationMethods", []):
                    return model["name"]
        except Exception as e:
            print(f"[Gemini API list models error]: {e}")
        return None

    def generate_ai_response(self, transcript):
        self.full_transcript.append({"role": "user", "content": transcript})
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.full_transcript])
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        model_name = "gemini-1.5-flash"
        endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        try:
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            print("[Gemini API raw response]", result)
            ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            ai_response = f"[Gemini API error]: {e}"
        self.generate_audio(ai_response)
        self.full_transcript.append({"role": "assistant", "content": ai_response})

    def generate_audio(self, text):
        print(f"\nAI Receptionist: {text}")
        try:
            audio_stream = generate(
                api_key=self.elevenlabs_api_key,
                text=text,
                stream=True
            )
            stream(audio_stream)
        except Exception as e:
            print(f"[Error in generate_audio]: {e}")

    def gtts_tts(self, text):
        try:
            from gtts import gTTS
            import io
            tts = gTTS(text)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            return buf.read()
        except Exception as e:
            print(f"[ERROR] gTTS failed: {e}")
            return b""

    def clean_markdown(self, text):
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\*(.*?)\*', r'\1', text)
        text = re.sub(r'`([^`]*)`', r'\1', text)
        text = re.sub(r'\[(.*?)\]\((.*?)\)', r'\1', text)
        return text

    def play_with_mpv(self, audio_bytes, filename="output.wav"):
        try:
            with open(filename, "wb") as f:
                f.write(audio_bytes)
            print(f"[DEBUG] Playing with mpv: {filename}")
            result = subprocess.run(["mpv", filename], capture_output=True, text=True)
            if result.returncode != 0:
                print(f"[ERROR] mpv playback failed: {result.stderr}")
        except Exception as e:
            print(f"[ERROR] mpv playback failed: {e}")

    def get_response_and_audio(self, user_text):
        self.full_transcript.append({"role": "user", "content": user_text})
        prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.full_transcript])
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        model_name = "gemini-1.5-flash"
        endpoint = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent"
        try:
            response = requests.post(endpoint, headers=headers, json=data)
            response.raise_for_status()
            result = response.json()
            ai_response = result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            ai_response = f"[Gemini API error]: {e}"
        self.full_transcript.append({"role": "assistant", "content": ai_response})
        clean_response = self.clean_markdown(ai_response)
        audio_bytes = self.gtts_tts(clean_response)
        print(f"[DEBUG] gTTS audio_bytes length: {len(audio_bytes)}")
        self.play_with_mpv(audio_bytes)
        return ai_response, audio_bytes

if __name__ == "__main__":
    assistant = AI_Assistant()
    assistant.start_transcription()



