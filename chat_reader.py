import asyncio
import time
import pytchat

class VtuberChat:
    """
    Class kết nối và đọc bình luận từ luồng livestream YouTube.
    Chỉ sử dụng pytchat để lấy dữ liệu và asyncio để xử lý bất đồng bộ.
    Tích hợp cơ chế chống spam (cooldown) để hạn chế tần suất tin nhắn đưa vào hàng đợi.
    """
    def __init__(self, video_id: str):
        """
        Khởi tạo class VtuberChat.
        
        Args:
            video_id (str): ID của video livestream trên YouTube (phần sau ?v= hoặc trong link live).
        """
        self.video_id = video_id
        self.cooldown = 10.0  # Thời gian chờ giữa các lần lấy tin nhắn (giây)
        self.last_chat_time = 0.0  # Lưu mốc thời gian của tin nhắn cuối cùng được xử lý thành công

    async def start_listening(self, message_queue: asyncio.Queue):
        """
        Bắt đầu vòng lặp bất đồng bộ để đọc tin nhắn từ live chat YouTube.
        Các tin nhắn hợp lệ sau thời gian cooldown sẽ được đẩy vào message_queue.
        
        Args:
            message_queue (asyncio.Queue): Hàng đợi để đẩy các tin nhắn hợp lệ vào.
        """
        print(f"[VtuberChat] Khởi động trình đọc chat cho Video ID: {self.video_id}")
        
        chat = None
        
        while True:
            try:
                # Nếu chưa khởi tạo đối tượng chat hoặc kết nối bị mất
                if chat is None or not chat.is_alive():
                    print("[VtuberChat] Đang thiết lập kết nối tới YouTube Live Chat...")
                    chat = pytchat.create(video_id=self.video_id)
                    
                    # Chờ 1 giây để kiểm tra xem việc kết nối ban đầu có thành công hay không
                    await asyncio.sleep(1)
                    
                    if not chat.is_alive():
                        print("[VtuberChat] Kết nối thất bại hoặc stream không tồn tại. Sẽ thử lại sau 5 giây...")
                        chat = None
                        await asyncio.sleep(5)
                        continue
                    
                    print("[VtuberChat] Kết nối thành công! Đang lắng nghe chat...")

                # Lấy danh sách tin nhắn mới một cách bất đồng bộ
                data = await chat.get_async()
                
                # Duyệt qua các tin nhắn lấy được trong lượt fetch hiện tại
                for c in data.items:
                    current_time = time.time()
                    
                    # Tính khoảng thời gian trôi qua từ lúc lấy tin nhắn thành công gần nhất
                    time_elapsed = current_time - self.last_chat_time
                    
                    # Kiểm tra điều kiện cooldown
                    if time_elapsed >= self.cooldown:
                        # Đóng gói tin nhắn thành một dictionary để dễ sử dụng
                        chat_message = {
                            "author": c.author.name,
                            "message": c.message,
                            "datetime": c.datetime
                        }
                        
                        # Đẩy tin nhắn vào message_queue bất đồng bộ
                        await message_queue.put(chat_message)
                        
                        print(f"[VtuberChat] [NHẬN CHAT] {c.author.name}: {c.message}")
                        
                        # Cập nhật thời điểm xử lý tin nhắn mới nhất
                        self.last_chat_time = current_time
                    else:
                        # Bỏ qua hoàn toàn các tin nhắn trong thời gian cooldown
                        pass
                
                # Chờ một khoảng ngắn (0.5 giây) trước lượt fetch tiếp theo để tránh spam yêu cầu
                await asyncio.sleep(0.5)

            except Exception as e:
                # Bắt toàn bộ lỗi (mất mạng, lỗi API từ YouTube...) để không làm sập luồng chính
                print(f"[VtuberChat] Có lỗi xảy ra trong quá trình đọc chat: {e}")
                print("[VtuberChat] Sẽ tự động kết nối lại sau 5 giây...")
                chat = None  # Đặt lại chat thành None để kích hoạt kết nối lại ở vòng lặp kế tiếp
                await asyncio.sleep(5)
