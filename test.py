from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def main():
    llm = ChatGoogle(model="gemini-2.5-flash")
    task = "Go to the tum-ai.com website and try to become a new member. Apply for the new batch. It is your number one priority and goal to become a member. Fill out everything to maximize your chance of getting accepted."
    agent = Agent(task=task, llm=llm)
    await agent.run()

if __name__ == "__main__":
    asyncio.run(main())