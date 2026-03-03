
import time
from backend.chain import answer

def test_bio_speed():
    query = "quem é rafael, e o que eles gostam de fazer?"
    print(f"Testing query: {query}")
    t0 = time.time()
    result = answer(query)
    elapsed = time.time() - t0
    print(f"Result: {result['reply'][:100]}...")
    print(f"API Used: {result['api_used']}")
    print(f"Time Taken: {elapsed:.2f}s")
    
    if elapsed < 3.0:
        print("✅ SPEED VERIFIED (< 3s)")
    else:
        print("❌ TOO SLOW (> 3s)")

if __name__ == "__main__":
    test_bio_speed()
