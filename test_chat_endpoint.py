import requests
import json

# Simple test for chat endpoint
response = requests.post(
    "http://localhost:8000/api/chat",
    json={
        "message": "Hello test",
        "top_k": 3,
        "search_sources": ["documents", "knowledge"]
    },
    stream=True,
    timeout=30
)

print(f"Status code: {response.status_code}")
print(f"Headers: {response.headers}")

if response.status_code == 200:
    print("\nStreaming response:")
    for i, line in enumerate(response.iter_lines()):
        if line:
            print(f"Line {i}: {line.decode('utf-8')}")
            if i > 20:  # Limit output
                print("... (truncated)")
                break
else:
    print(f"Error response: {response.text}")
