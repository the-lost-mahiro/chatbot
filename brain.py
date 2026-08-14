import os
import json
import time
import asyncio
import re

from llm_gemini import GeminiClient
from llm_ollama import OllamaClient

from mood import VtuberMood
from body import VtuberBody
from voice import VtuberVoice
from ear import VtuberEar
from chat_reader import VtuberChat

class VtuberBrain:
    def __init__(self, local_ai=False):
        if local_ai:
            self.llm = OllamaClient(model_name="qwen3:8b")
            print("🚀 Đang dùng AI Local (Ollama)")
        else:
            self.llm = GeminiClient()
            print("☁️ Đang dùng AI Cloud (Gemini)")

        self.history_file = 'memory.json'
        self.history = self._load_memory() # Tải lại ký ức khi khởi động

        with open("character_background.txt", "r", encoding="utf-8") as f: # Mở file background
                self.system_instruction_content = f.read().strip()

        self.last_interaction_time = time.time() # Lần cuối tương tác
        self.idle_threhold = 900 # 900s ~ 15p
        self.is_processing = False

        self.voice_box = VtuberVoice() # Voice
        self.mood_engine = VtuberMood() # Hệ thống cảm xúc
        self.body = VtuberBody()

    def clean_text(self, text):
        # Xóa các ký tự không phải chữ cái, số hoặc dấu câu cơ bản
        return re.sub(r'[^\w\s,.?!]', '', text)

    def _load_memory(self):
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return [] # Nếu chưa có file thì bắt đầu với bộ nhớ trống

    def _save_memory(self):
        with open(self.history_file, "w", encoding = "utf-8") as f:
            json.dump(self.history, f, ensure_ascii = False, indent = 4)

    def _parse_response(self, response_text: str) -> dict:
        try:
            # Decode JSON
            return json.loads(response_text)
        
        except json.JSONDecodeError:
            # Nếu lỗi, thử lọc bỏ Markdown (```json ... ```)
            try:
                clean_json = re.sub(r'```json|```', '', response_text).strip()
                return json.loads(clean_json)
            
            except:
                # Nếu nát quá thì coi như là text thuần
                print(f"⚠️ Lỗi JSON, dùng chế độ Fallback. Text gốc: {response_text[:50]}...")
                return {
                    "display_text": response_text, 
                    "voice_text": response_text, 
                    "emotion": "default"
                }

    def commands(self, cmd: str): #Local command
        cmd = cmd.lower().strip()

        if cmd == '/reset':
            self.history = []
            self._save_memory()
            return '🧹 Hệ thống đã được xóa sạch bộ nhớ!'
        
        elif cmd == '/status':
            llm_name = self.llm.__class__.__name__
            return f"🤖 Model: {llm_name} | Memory: {len(self.history)} messages."
        
        elif cmd == "/help":
            return "📌 Lệnh hiện có: /reset, /status, /help, /exit"
        
        else:
            return "❓ Lệnh không hợp lệ. Gõ /help để xem danh sách."
    
    @staticmethod
    async def typewriter_print(text, delay = 0.05):
        # In chữ theo kiểu máy đánh chữ
        print("Not-Neuro: ", end='', flush = True)

        for char in text:
            print(char, end='', flush = True)
            await asyncio.sleep(delay)

        print("\n")
    
    async def perform_action(self, data: dict):
        display_text = data.get("display_text", "Mahiro ơi lỗi rồi!")
        voice_text = data.get("voice_text", "Mahiro ơi lỗi rồi!")
        emotion = data.get("emotion", "default")

        # Cập nhật mood và giọng
        self.mood_engine.update(emotion)
        rate, pitch = self.mood_engine.convert()
        mood_info = self.mood_engine.get_mood_bar()
        print(f"\n{mood_info}")

        # 1. Chuẩn bị Audio
        clean_voice = self.voice_box.clean_text(voice_text)
        is_audio_ready = await self.voice_box.prepare_audio(clean_voice, rate, pitch)

        if is_audio_ready:
            # 2. Audio xong -> Đổi mặt
            hotkey_map = {
                "happy": "Happy", 
                "sad": "Sad", 
                "angry": "Angry", 
                "default": "Default"
            }
            target_hotkey = hotkey_map.get(emotion)
            
            if target_hotkey:
                await self.body.trigger_hotkey(target_hotkey, duration=7)

            # 3. Phát tiếng + Nhép môi
            self.voice_box.play()
            
            # Tạo task nhép môi chạy song song
            sync_task = asyncio.create_task(self.body.lip_sync(self.voice_box.is_playing))
            
            # Chạy chữ kiểu máy đánh chữ
            await self.typewriter_print(display_text)

            # Chờ nói xong
            while self.voice_box.is_playing():
                await asyncio.sleep(0.1)

            await sync_task # Dừng nhép môi
            self.voice_box.stop_and_clear()

            # Tắt biểu cảm
            if target_hotkey:
                await self.body.trigger_hotkey(target_hotkey)
        else:
            # Nếu lỗi Audio thì chỉ hiện text
            await self.typewriter_print(display_text)
        
    async def autonomy_mode(self):
        while True:
            await asyncio.sleep(5)

            current_time = time.time()
            silence_duration = current_time - self.last_interaction_time

            if not self.is_processing and silence_duration > self.idle_threhold:
                self.is_processing = True # Lock

                try:
                    autonomy_prompt = (
                        "User đã im lặng 15 phút rồi. "
                        "Hãy tự nghĩ ra một câu nói ngắn (dưới 20 từ) để bắt chuyện một cách tự nhiên. "
                        "Ví dụ: than thở chán, hỏi user đang làm gì, hoặc kể một fact ngắn thú vị. "
                        "Đừng lặp lại câu cũ."
                        "Trả về định dạng JSON chuẩn như mọi khi."
                    )
                    json_string = await self.llm.generate_response(
                        self.system_instruction_content, 
                        self.history, 
                        autonomy_prompt
                    )
                    data = self._parse_response(json_string)

                    print(f"🤖 [Bot Tự Nghĩ]: {data.get('display_text')}")

                    self.history.append({"role": "bot", "text": data.get("display_text")})

                    self._save_memory() # Optional

                    await self.perform_action(data)

                except Exception as e:
                    print(f"❌ Lỗi Autonomy: {e}")

                finally:
                    self.last_interaction_time = time.time()
                    self.is_processing = False # Unlock
                    

    async def process_chat(self, user_input: str):
        # Đảm bảo cơ thể đã kết nối ONE-TIME
        if not self.body.vts:
            await self.body.connect()

        self.is_processing = True
        try:
            json_string = await self.llm.generate_response(
                self.system_instruction_content, 
                self.history, 
                user_input
            )

            data = self._parse_response(json_string)
            
            # Cập nhật lịch sử mới
            self.history.append({"role": "user", "text": user_input})
            self.history.append({"role": "bot", "text": data.get('display_text')})

            self._save_memory()

            await self.perform_action(data)

            return {"status": "success"}
        
        except Exception as e:
            print(f"❌ Lỗi chat: {e}")
            return {"status": "error"}

        finally:
            self.last_interaction_time = time.time() # Reset time
            self.is_processing = False

    async def run(self):
        print("=== TERMINAL ===")

        await self.body.connect()

        self.ear = VtuberEar()

        print("Chọn chế độ: [1] Chat  |  [2] Mic  |  [3] YouTube Live")
        mode = input("Nhập 1/2/3: ").strip()
        
        asyncio.create_task(self.autonomy_mode())

        if mode == '3':
            video_id = input("Nhập Video ID của YouTube Live (VD: dQw4w9WgXcQ): ").strip()
            
            # Tạo một cái giỏ (Queue) để đựng tin nhắn
            chat_queue = asyncio.Queue()
            
            # Khởi tạo người đọc chat
            youtube_reader = VtuberChat(video_id)
            
            # Bật task đọc chat chạy ngầm liên tục, ném tin vào chat_queue
            asyncio.create_task(youtube_reader.start_listening(chat_queue))
            
            print("🔴 Đang chờ comment từ luồng Live...")
            
            # Vòng lặp chính của Brain
            while True:
                self.last_interaction_time = time.time()
                
                # Hàm get() sẽ đứng chờ ở đây cho đến khi có comment trong Queue
                user_input = await chat_queue.get() 
                
                print(f" -> Khán giả chat: {user_input}")
                
                if user_input == '/exit':
                    await self.body.close()
                    break
                    
                # Xử lý câu chat bằng Gemini (như cũ)
                await self.process_chat(user_input)

        else:
            while True:
                user_input = ''

                if mode == '2':
                    user_input = await asyncio.to_thread(self.ear.listen)

                    if user_input: 
                        print(f" -> Bạn nói: {user_input}")

                    else:
                        # Nếu không nghe thấy gì thì bỏ qua vòng lặp, nghe lại
                        await asyncio.sleep(0.1) 
                        continue
                else:
                    print("User: ", end='', flush=True)
                    # run_in_executor -> input không chặn Autonomy loop
                    loop = asyncio.get_running_loop()
                    user_input = await loop.run_in_executor(None, input)

                self.last_interaction_time = time.time()

                if not user_input: continue # Empty String

                if user_input.startswith('/'): # Check command
                    if user_input == '/exit':
                        await self.body.close()
                        break

                    result = self.commands(user_input)
                    print(f'SYSTEM: {result}\n')

                else:
                    await self.process_chat(user_input)