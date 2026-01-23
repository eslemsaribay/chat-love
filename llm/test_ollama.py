"""Quick test script to verify Ollama integration works."""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import llm
sys.path.insert(0, str(Path(__file__).parent.parent))

from llm import initialize_llm, chat, shutdown_llm


def main():
    print("=" * 60)
    print("LLM Integration Test - Ollama Backend")
    print("=" * 60)
    print()

    # Test 1: Initialize
    print("1. Testing initialization...")
    try:
        initialize_llm(model_path="llama3.2")
        print("   ✓ Initialization successful")
    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        print()
        print("Make sure:")
        print("  1. Ollama is installed: https://ollama.com/download")
        print("  2. Ollama is running (should start automatically)")
        print("  3. You've pulled the model: ollama pull llama3.2")
        return

    print()

    # Test 2: Simple chat
    print("2. Testing simple chat...")
    try:
        response = chat("Say 'Hello from TouchDesigner!' in one short sentence.")
        print(f"   ✓ Response: {response}")
    except Exception as e:
        print(f"   ✗ Chat failed: {e}")
        shutdown_llm()
        return

    print()

    # Test 3: Multi-turn conversation
    print("3. Testing multi-turn conversation...")
    try:
        response = chat("What is your previous message?")
        print(f"   ✓ Response: {response}")
    except Exception as e:
        print(f"   ✗ Multi-turn failed: {e}")

    print()

    # Test 4: Shutdown
    print("4. Testing shutdown (saves conversation)...")
    try:
        shutdown_llm()
        print("   ✓ Shutdown successful")
    except Exception as e:
        print(f"   ✗ Shutdown failed: {e}")

    print()
    print("=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  - Check conversation_logs/ for saved conversation")
    print("  - Try the examples in README.md")
    print("  - Integrate with TouchDesigner!")


if __name__ == "__main__":
    main()
