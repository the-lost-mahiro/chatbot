import asyncio
from dotenv import load_dotenv
from brain import VtuberBrain

load_dotenv()

if __name__ == "__main__":
    my_vtuber = VtuberBrain(local_ai=True)
    asyncio.run(my_vtuber.run())