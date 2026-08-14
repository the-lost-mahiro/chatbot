import speech_recognition as sr

class VtuberEar:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone() 
        
        # Tự động lọc tiếng ồn (tùy chọn)
        # with self.microphone as source:
        #     self.recognizer.adjust_for_ambient_noise(source)

    def listen(self):
        try:
            with self.microphone as source:
                print("Đang lắng nghe...")
                
                # Lọc tiếng quạt gió/tiếng ồn nền trong 0.5s trước khi nghe
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # nghe tối đa 10s (phrase_time_limit) để tránh treo nếu ồn quá
                # timeout=5 nghĩa là nếu 5s không ai nói gì thì bỏ qua
                audio_data = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

                print("Đang dịch sang chữ...")
                # Gửi lên Google API (Cần mạng)
                text = self.recognizer.recognize_google(audio_data, language="vi-VN")
                
                # Trả về chữ thường để dễ xử lý lệnh
                return text.lower()

        except sr.WaitTimeoutError:
            print("⚠️ Không nghe thấy gì (Timeout)")
            return ""
            
        except sr.UnknownValueError:
            print("⚠️ Không hiểu bạn nói gì (Có thể do ồn)")
            return ""
            
        except sr.RequestError:
            print("❌ Lỗi mạng hoặc lỗi API Google")
            return ""
        
        except Exception as e:
            print(f"❌ Lỗi lạ: {e}")
            return ""