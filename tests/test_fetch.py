import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

# We need to simulate the package structure context if we want relative imports to work perfectly,
# but since we are running this from root, we can import src.tools if we are careful.
# However, src.tools imports .database.
# Ideally we run this as a module: python -m custom_test
# Let's try basic import first. Since we are in root, 'import src.tools' deals with 'src' as package.
# References inside tools.py like 'from .database' will resolve to src.database.

try:
    from src.tools import fetch_url
except ImportError as e:
    # If this fails, we might need to adjust sys.path
    import sys
    sys.path.append(os.getcwd())
    from src.tools import fetch_url

# Mock RunContext
class MockContext:
    def __init__(self):
        self.deps = {}

async def main():
    ctx = MockContext()
    url = "https://www.example.com"
    print(f"Fetching {url}...")
    try:
        result = await fetch_url(ctx, url)
        print("Result:")
        print(result)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
