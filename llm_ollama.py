import json
import asyncio

import ollama 
from llm_base import BaseLLM

class OllamaClient(BaseLLM):
    def __init__(self, model_name="qwen3:4b"): # Hoặc gemma, qwen tùy bạn cài
        self.model_name = model_name

    async def generate_response(self, system_instruction: str, history: list, user_input: str) -> str:
        # 1. Dịch lịch sử sang chuẩn của Ollama (giống hệt OpenAI)
        ollama_messages = [
            {"role": "system", "content": system_instruction}
        ]
        
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            ollama_messages.append({"role": role, "content": msg["text"]})
            
        ollama_messages.append({"role": "user", "content": user_input})

        # 2. Yêu cầu Ollama trả về JSON
        # Chạy trong luồng phụ để không block async loop
        def run_ollama():
            return ollama.chat(
                model=self.model_name,
                messages=ollama_messages,
                format='json',
                options={"temperature": 0.7}
            )
            
        response = await asyncio.to_thread(run_ollama)
        return response['message']['content'] # Trả về chuỗi JSON thô