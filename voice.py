import os
import uuid
import asyncio
import pygame
import re
import edge_tts
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings

class VtuberVoice:
    def __init__(self):
        # self.api_key = os.getenv("ELEVENLABS_API_KEY")
        # self.voice_id = os.getenv("ELEVENLABS_VOICE_ID")
        
        # # Kiểm tra Key
        # if not self.api_key or not self.voice_id:
        #     print("⚠️ CẢNH BÁO: Thiếu ELEVENLABS_API_KEY hoặc ELEVENLABS_VOICE_ID trong .env")
        # else:
        #     # Khởi tạo Client ElevenLabs
        #     self.client = ElevenLabs(api_key = self.api_key)

        if not pygame.mixer.get_init(): # Chỉ khởi tạo mixer một lần duy nhất khi tạo object
            pygame.mixer.init()
        
        self.voice_name = 'vi-VN-HoaiMyNeural'
        self.audio_file = None

    def clean_text(self, text):
        """Lọc bỏ icon để tránh TTS đọc lỗi"""
        cleaned = re.sub(r'[^\w\s,.?!]', '', text).strip()
        if not cleaned.endswith(('.', '!', '?')):
            cleaned += '.' 
        return cleaned
    
    async def prepare_audio(self, text: str, rate: str, pitch: str):
        # if not hasattr(self, 'client'):
        #     print("❌ Chưa khởi tạo được ElevenLabs Client (Thiếu Key).")
        #     return False
        
        try:
            self.audio_file = f"speech_{uuid.uuid4().hex}.mp3"
            communicate = edge_tts.Communicate(
                text=text, 
                voice=self.voice_name, 
                rate=rate, 
                pitch=pitch
            )

            await communicate.save(self.audio_file)
            
            return True

            # def generate_elevenlabs():
            #     audio_generator = self.client.text_to_speech.convert(
            #         voice_id=self.voice_id,
            #         model_id="eleven_multilingual_v2", # Model hỗ trợ tiếng Việt tốt nhất
            #         text=text,
            #         voice_settings=VoiceSettings(
            #             stability = 0.5,       # Độ ổn định (thấp = nhiều cảm xúc, cao = đều)
            #             similarity_boost = 0.75, # Độ giống giọng gốc
            #             style = 0.0,
            #             use_speaker_boost = True
            #         )
            #     )
            #     # Lưu stream thành file
            #     with open(filename, "wb") as f:
            #         for chunk in audio_generator:
            #             if chunk:
            #                 f.write(chunk)
            #     return filename

            # # Chạy hàm blocking trong luồng riêng để không chặn Async (không làm đơ)
            # await asyncio.to_thread(generate_elevenlabs)

            # self.audio_file = filename
            # return True

        except Exception as e:
            print(f"❌ Lỗi tạo voice: {e}")
            return False
        
    def play(self):
        try:
            if self.audio_file and os.path.exists(self.audio_file):
                pygame.mixer.music.load(self.audio_file) # Phát file
                pygame.mixer.music.play()

        except Exception as e:
            print(f"❌ Lỗi phát voice: {e}")
    
    def is_playing(self):
        # Kiểm tra xem còn nói không
        return pygame.mixer.music.get_busy()
    
    def stop_and_clear(self):
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload() # Giải phóng file

            if self.audio_file and os.path.exists(self.audio_file):
                os.remove(self.audio_file)
                self.audio_file = None

        except Exception as e:
            print(f"⚠️ Lỗi dọn dẹp file âm thanh: {e}")