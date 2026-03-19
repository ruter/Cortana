import asyncio
import time
from src.conversation_cache import ConversationState, CachedMessage

async def main():
    state = ConversationState(user_id="test_user")
    state.messages.append(CachedMessage(role="user", content="Hello world!"))
    state.compact_summary = "A summary of the conversation history goes here."

    start = time.time()
    for _ in range(100):
        state.calculate_tokens("openai/gpt-4o")
    end = time.time()

    print(f"Time taken: {end - start:.4f} seconds")
    print(f"Total tokens: {state.total_tokens}")

asyncio.run(main())
