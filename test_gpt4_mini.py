import requests
import time
import json

API_URL = "http://localhost:8000/api/chat"
conversation_id = "test-gpt4-mini-performance"

test_questions = [
    "癒몄떊?щ떇怨??λ윭?앹쓽 李⑥씠?먯쓣 ?ㅻ챸?댁＜?몄슂.",
    "RESTful API ?ㅺ퀎 ?먯튃??????ㅻ챸?댁＜?몄슂.",
    "Docker? Kubernetes??李⑥씠?먯? 臾댁뾿?멸???"
]

print("=" * 80)
print("GPT-4o-mini ?깅뒫 ?뚯뒪???쒖옉")
print("=" * 80)

results = []

for i, question in enumerate(test_questions, 1):
    print(f"\n[?뚯뒪??{i}/3]")
    print(f"吏덈Ц: {question}")
    print("-" * 80)
    
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            json={
                "message": question,
                "conversation_id": f"{conversation_id}-{i}"
            },
            timeout=60
        )
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("response", "")
            
            # 留덊겕?ㅼ슫 援ъ“ 遺꾩꽍
            has_headers = "##" in answer or "###" in answer
            has_lists = ("- " in answer or "* " in answer or 
                        ". " in answer and any(c.isdigit() for c in answer))
            has_code_blocks = "```" in answer
            
            print(f"???묐떟 ?쒓컙: {elapsed_time:.2f}珥?)
            print(f"???묐떟 湲몄씠: {len(answer)}??)
            print(f"??留덊겕?ㅼ슫 ?ㅻ뜑: {'?덉쓬' if has_headers else '?놁쓬'}")
            print(f"??留덊겕?ㅼ슫 由ъ뒪?? {'?덉쓬' if has_lists else '?놁쓬'}")
            print(f"??肄붾뱶 釉붾줉: {'?덉쓬' if has_code_blocks else '?놁쓬'}")
            print(f"\n?묐떟 誘몃━蹂닿린 (泥섏쓬 500??:")
            print(answer[:500])
            
            results.append({
                "test_number": i,
                "question": question,
                "response_time": elapsed_time,
                "response_length": len(answer),
                "has_markdown_structure": has_headers or has_lists,
                "has_code_blocks": has_code_blocks,
                "success": True
            })
        else:
            print(f"???ㅻ쪟: HTTP {response.status_code}")
            print(f"?묐떟: {response.text}")
            results.append({
                "test_number": i,
                "question": question,
                "error": f"HTTP {response.status_code}",
                "success": False
            })
    
    except Exception as e:
        print(f"???ㅻ쪟 諛쒖깮: {str(e)}")
        results.append({
            "test_number": i,
            "question": question,
            "error": str(e),
            "success": False
        })
    
    # ?ㅼ쓬 ?뚯뒪?????좎떆 ?湲?    if i < len(test_questions):
        time.sleep(2)

# 寃곌낵 ?붿빟
print("\n" + "=" * 80)
print("?깅뒫 ?뚯뒪??寃곌낵 ?붿빟")
print("=" * 80)

successful_tests = [r for r in results if r.get("success", False)]

if successful_tests:
    avg_response_time = sum(r["response_time"] for r in successful_tests) / len(successful_tests)
    min_response_time = min(r["response_time"] for r in successful_tests)
    max_response_time = max(r["response_time"] for r in successful_tests)
    
    print(f"\n?깃났???뚯뒪?? {len(successful_tests)}/{len(results)}")
    print(f"\n?묐떟 ?쒓컙:")
    print(f"  - ?됯퇏: {avg_response_time:.2f}珥?)
    print(f"  - 理쒖냼: {min_response_time:.2f}珥?)
    print(f"  - 理쒕?: {max_response_time:.2f}珥?)
    print(f"  - 10珥??대궡 紐⑺몴: {'???ъ꽦' if avg_response_time <= 10 else '??誘몃떖??}")
    
    markdown_count = sum(1 for r in successful_tests if r.get("has_markdown_structure", False))
    code_block_count = sum(1 for r in successful_tests if r.get("has_code_blocks", False))
    
    print(f"\n留덊겕?ㅼ슫 援ъ“:")
    print(f"  - 援ъ“?붾맂 ?묐떟: {markdown_count}/{len(successful_tests)}")
    print(f"  - 肄붾뱶 釉붾줉 ?ы븿: {code_block_count}/{len(successful_tests)}")
else:
    print("\n紐⑤뱺 ?뚯뒪?멸? ?ㅽ뙣?덉뒿?덈떎.")

print("\n" + "=" * 80)
