import numpy as np
import random

class VtuberMood:
    def __init__(self):
        # Khởi tạo Vector tâm trạng 2D
        # Quy ước: [Valence (Vui/Buồn), Arousal (Năng lượng)]
        self.mood_vector = np.array([0.0, 0.0], dtype = np.float32)

        # Giới hạn % tăng rate và Hz của pitch
        self.max_rate = 30
        self.max_pitch = 50

        self.base_rate = +25

        # Map ảnh hưởng lên lời nói
        self.impact_map = {
            'happy': np.array([0.3, 0.2]),
            "sad": np.array([-0.3, -0.2]),
            "angry": np.array([-0.4, 0.5]),
            "default": np.array([0.0, 0.0])
        }
    
    def update(self, emotion_key): # Cập nhật tâm trạng
        impact = self.impact_map.get(emotion_key, self.impact_map["default"]) # Lấy impact từ cảm xúc, không có thì trả default
        
        # Quy ước: Mood_new = Old + Impact
        self.mood_vector = np.add(self.mood_vector, impact)

        # Đảm bảo tâm trạng nằm trong [-1, 1]
        self.mood_vector = np.clip(self.mood_vector, -1.0, 1.0)

    def convert(self): # Chuyển tâm trạng thành thông số của giọng nói
        valence, arousal = self.mood_vector
        
        # Thêm biến động ngẫu nhiên để giọng không bị "công nghiệp"
        rand_rate = random.uniform(-0.1, 0.1) # +/- 10%
        rand_pitch = random.uniform(-0.05, 0.05) # +/- 5Hz

        # Tính toán
        final_rate = int((valence * 0.5 + rand_rate) * self.max_rate) + self.base_rate
        final_pitch = int((arousal * 0.8 + rand_pitch) * self.max_pitch)

        # Kẹp giá trị hợp lý
        final_rate = max(min(final_rate, 80), -30) # Max +80%, Min -30%
        final_pitch = max(min(final_pitch, 50), -50)

        return f'{final_rate:+}%', f'{final_pitch:+}Hz'
    
    def get_mood_bar(self):
        # Dùng NumPy để tạo thanh tiến trình hiển thị tâm trạng
        valence = self.mood_vector[0]
        # Chuyển từ khoảng [-1, 1] sang [0, 20] để vẽ 20 vạch
        bar_length = 20
        filled_length = int(np.interp(valence, [-1, 1], [0, bar_length])) # Dùng hàm nội suy của NumPy
        
        bar = '█' * filled_length + '-' * (bar_length - filled_length)
        mood_name = "VUI" if valence > 0 else "BUỒN"
        if abs(valence) < 0.2: mood_name = "BÌNH THƯỜNG"
        
        return f"Tâm trạng: [{bar}] {int(filled_length*5)}% | {mood_name}"