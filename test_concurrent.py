import asyncio
import aiohttp
import random
import uuid

API_URL = "http://127.0.0.1:8000/api/enroll"
STATUS_URL = "http://127.0.0.1:8000/api/status/{}"
COMMISSION_ID = 4  # Com 4, quota 200. We will test sending 300 requests
TOTAL_CONCURRENT_REQUESTS = 300

async def submit_enrollment(session, i):
    dni = f"99{random.randint(100000, 999999)}"
    # Adding a small chance of duplicate DNI to test that constraint
    if i % 20 == 0:
        dni = "99000000"
        
    email = f"student_{i}_{uuid.uuid4().hex[:6]}@test.com"
    data = {
        "dni": dni,
        "apellido": f"TestApp_{i}",
        "nombre": f"TestNom_{i}",
        "email": email,
        "commission_id": COMMISSION_ID
    }
    
    async with session.post(API_URL, data=data) as response:
        if response.status == 200:
            res_json = await response.json()
            return res_json.get("task_id")
        return None

async def track_task(session, task_id):
    while True:
        async with session.get(STATUS_URL.format(task_id)) as response:
            if response.status == 200:
                res_json = await response.json()
                if res_json.get("status") == "completed":
                    if res_json.get("result", {}).get("success"):
                        return "enrolled"
                    else:
                        return f"failed_business_logic: {res_json.get('result', {}).get('error')}"
                elif res_json.get("status") == "error":
                    return "internal_error"
            await asyncio.sleep(0.5)

async def run_scenario():
    print(f"Starting {TOTAL_CONCURRENT_REQUESTS} concurrent requests for Com 4 (Quota 200)...")
    async with aiohttp.ClientSession() as session:
        # Submit concurrently
        tasks = [submit_enrollment(session, i) for i in range(TOTAL_CONCURRENT_REQUESTS)]
        task_ids = await asyncio.gather(*tasks)
        
        valid_task_ids = [t for t in task_ids if t]
        print(f"Submitted {len(valid_task_ids)} valid tasks to queue")
        
        # Track until all finish
        polls = [track_task(session, t) for t in valid_task_ids]
        results = await asyncio.gather(*polls)
        
        enrolled = results.count("enrolled")
        business_failed = sum(1 for r in results if str(r).startswith("failed_business"))
        internal_err = results.count("internal_error")
        
        print("\n--- TEST RESULTS ---")
        print(f"Successfully Enrolled: {enrolled}")
        print(f"Business Logic Rejected: {business_failed}")
        print(f"Internal Errors: {internal_err}")
        
        if enrolled <= 200 and internal_err == 0:
            print("CONCURRENCY TEST PASSED! No database locks occurred, quota is respected.")
        else:
            print("TEST FAILED.")

if __name__ == "__main__":
    asyncio.run(run_scenario())
