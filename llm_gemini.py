import os
from google import genai
from google.genai import types
from llm_base import BaseLLM

class GeminiClient(BaseLLM):
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.5-flash"

    async def generate_response(self, system_instruction: str, history: list, user_input: str) -> str:
        # 1. Dịch lịch sử trung lập sang chuẩn của Gemini
        gemini_history = []
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({"role": role, "parts": [{"text": msg["text"]}]})

        # 2. Cấu hình Prompt và ép kiểu JSON
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            temperature=0.7
        )

        # 3. Tạo phiên chat ảo để gọi API
        chat = self.client.aio.chats.create(
            model=self.model_id, 
            config=config, 
            history=gemini_history
        )
        
        response = await chat.send_message(user_input)
        return response.text # Trả về chuỗi JSON thô