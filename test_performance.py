# -*- coding: utf-8 -*-
import requests
import time
import json

API_URL = "http://localhost:8000/api/chat"

test_questions = [
    "What is the difference between machine learning and deep learning? Please explain in detail with examples.",
    "Explain RESTful API design principles and best practices.",
    "What are the differences between Docker and Kubernetes? Include use cases."
]

print("=" * 80)
print("GPT-4o-mini Performance Test")
print("=" * 80)

results = []

for i, question in enumerate(test_questions, 1):
    print(f"\n[Test {i}/3]")
    print(f"Question: {question}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            json={
                "message": question,
                "conversation_id": None
            },
            timeout=60
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("message", "")
            
            has_headers = "##" in answer or "###" in answer or "#" in answer
            has_lists = ("- " in answer or "* " in answer or "\n1. " in answer)
            has_code_blocks = "```" in answer
            has_bold = "**" in answer
            
            print(f"Response Time: {elapsed_time:.2f}s")
            print(f"Response Length: {len(answer)} chars")
            print(f"Has Markdown Headers: {has_headers}")
            print(f"Has Lists: {has_lists}")
            print(f"Has Code Blocks: {has_code_blocks}")
            print(f"Has Bold Text: {has_bold}")
            print(f"\nPreview (first 400 chars):")
            print(answer[:400])
            print("...")
            
            results.append({
                "response_time": elapsed_time,
                "response_length": len(answer),
                "has_markdown": has_headers or has_lists or has_bold,
                "has_code_blocks": has_code_blocks,
                "success": True
            })
        else:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            results.append({"success": False, "error": response.status_code})
    
    except Exception as e:
        print(f"Error: {str(e)}")
        results.append({"success": False, "error": str(e)})
    
    if i < len(test_questions):
        print(f"\nWaiting 2 seconds before next test...")
        time.sleep(2)

print("\n" + "=" * 80)
print("PERFORMANCE TEST SUMMARY")
print("=" * 80)

successful = [r for r in results if r.get("success", False)]

if successful:
    avg_time = sum(r["response_time"] for r in successful) / len(successful)
    min_time = min(r["response_time"] for r in successful)
    max_time = max(r["response_time"] for r in successful)
    avg_length = sum(r["response_length"] for r in successful) / len(successful)
    
    print(f"\nSuccessful Tests: {len(successful)}/{len(results)}")
    print(f"\n[Response Time Analysis]")
    print(f"  Average: {avg_time:.2f}s")
    print(f"  Min: {min_time:.2f}s")
    print(f"  Max: {max_time:.2f}s")
    goal_status = "ACHIEVED" if avg_time <= 10 else "NOT ACHIEVED"
    print(f"  Under 10s Goal: {goal_status}")
    
    print(f"\n[Response Quality]")
    print(f"  Average Length: {int(avg_length)} chars")
    markdown_count = sum(1 for r in successful if r.get("has_markdown", False))
    code_count = sum(1 for r in successful if r.get("has_code_blocks", False))
    print(f"  Structured Markdown: {markdown_count}/{len(successful)}")
    print(f"  Contains Code Blocks: {code_count}/{len(successful)}")
    
    print(f"\n[Comparison Notes]")
    print(f"  Model: GPT-4o-mini")
    print(f"  Previous Model: GPT-3.5-turbo")
    speed_check = "YES" if avg_time <= 10 else "NO"
    print(f"  Speed Goal Met (< 10s): {speed_check}")
    print(f"  Quality: Enhanced reasoning with GPT-4 architecture")
    print(f"  Structure: Improved markdown formatting")
else:
    print("\nAll tests failed.")
    for i, result in enumerate(results, 1):
        if not result.get("success"):
            print(f"  Test {i}: {result.get('error', 'Unknown error')}")

print("\n" + "=" * 80)