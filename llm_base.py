from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    async def generate_response(self, system_instruction: str, history: list, user_input: str) -> str:
        """
        Hàm này bắt buộc phải trả về một chuỗi dạng JSON (string) 
        có cấu trúc: {"display_text": "...", "voice_text": "...", "emotion": "..."}
        
        - history: danh sách dict trung lập, vd: [{"role": "user", "text": "chào"}, {"role": "bot", "text": "hi"}]
        """
        pass