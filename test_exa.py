import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

try:
    from src.tools import search_web_exa, get_contents_exa
except ImportError:
    import sys
    sys.path.append(os.getcwd())
    from src.tools import search_web_exa, get_contents_exa

class MockContext:
    def __init__(self):
        self.deps = {}

async def main():
    ctx = MockContext()
    
    print("--- Testing Search ---")
    try:
        if not os.getenv("EXA_API_KEY"):
            print("Skipping test: EXA_API_KEY not found in environment.")
        else:
            result = await search_web_exa(ctx, "latest AI news")
            print(result)
            
            print("\n--- Testing Get Contents ---")
            # Extract a URL from result if possible, or use a dummy one
            # For simplicity, let's use a known one or just test the call
            result = await get_contents_exa(ctx, ["https://www.google.com"])
            print(result[:500] + "...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
