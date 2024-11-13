import asyncio
import httpx
import json
import time
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# OpenRouter API settings
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Redis Service URL
REDIS_SERVICE_URL = "https://parkservice.mintcocoa.cc/redis/api"

# Facility Service URL
FACILITY_SERVICE_URL = "https://parkservice.mintcocoa.cc/facilities/api"

# Headers for OpenRouter API
OPENROUTER_HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

# Headers for Facility Service
FACILITY_HEADERS = {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
}

async def get_ride_info(ride_id):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{REDIS_SERVICE_URL}/ride_info/{ride_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            print(f"Failed to get ride info for {ride_id}: {exc}")
            return None

async def send_ai_prompt(all_rides_info, previous_warnings=None):
    print("\n[AI 요청] 모든 놀이기구 상태 분석")
    
    # 이전 경고 메시지가 있다면 프롬프트에 포함
    warning_message = ""
    if previous_warnings:
        warning_message = "\nPrevious decision warnings:\n" + "\n".join(previous_warnings) + "\n"
        print("[AI 요청] 이전 결정의 문제점 포함")
        print(warning_message)

    facilities_status = []
    for ride in all_rides_info:
        status = (
            f"The current status of the '{ride['name']}' ride in the amusement park simulation is as follows:\n"
            f"- Number of people in queue: {ride['queue_length']}\n"
            f"- Number of riders currently on the ride: {ride['active_riders']}\n"
            f"- Maximum capacity of the ride: {ride['max_capacity']}\n"
            f"- Estimated wait time: {ride['estimated_wait_time']} minutes\n\n"
            "The number of people in the queue must not exceed the maximum capacity of the ride.\n"
            "choose start boarding when queue_length is more than 0 and no active_riders.\n "
            "this means start boarding is only when the queue is not empty and no riders are on the ride.\n "
            "After boarding, you must disembarkation ride to people board again that all riders are off the ride.\n "
            "choose do nothing only when the queue is empty\n "
            
            "Based on this information, analyze the situation and respond with ONLY the number:\n"
            "1 - start boarding.\n"
            "2 - disembarkation ride.\n"
            "3 - do nothing.\n"
        )
        facilities_status.append(status)
    
    combined_prompt = (
        "Analyze each ride and provide decisions in order, separated by commas.\n" +
        warning_message +  # 이전 경고 메시지 추가
        "\n=====\n".join(facilities_status) +
        "\nImportant: Respond with ONLY numbers separated by commas (e.g., '1,2,3,1') without any additional text."
    )

    data = {
        "model": "google/gemini-flash-1.5-8b",
        "messages": [
            {
                "role": "user",
                "content": combined_prompt
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            print("[API 요청] OpenRouter API 호출 중...")
            response = await client.post(OPENROUTER_API_URL, headers=OPENROUTER_HEADERS, json=data)
            response.raise_for_status()
            response_json = response.json()
            print("[API 응답] 응답 수신 완료")
            ai_response = response_json['choices'][0]['message']['content']
            print(f"[AI 결정] 응답: {ai_response}")
            return ai_response.strip().split(',')
        except httpx.HTTPError as exc:
            print(f"[오류] AI 응답 실패: {exc}")
            return None

async def monitor_queues():
    while True:
        facilities = await get_active_facilities()
        all_rides_info = []
        
        # 모든 시설의 정보를 한 번에 수집
        async with httpx.AsyncClient() as client:
            for facility in facilities:
                ride_info = await get_ride_info(facility['id'])
                if ride_info:
                    combined_info = {
                        'id': facility['id'],
                        'name': ride_info.get('facility_name', 'Unknown'),
                        'duration': ride_info.get('ride_duration', 0),
                        'max_capacity': int(ride_info.get('max_capacity', 0)),
                        'queue_length': int(ride_info.get('current_waiting_riders', 0)),
                        'active_riders': int(ride_info.get('current_active_riders', 0)),
                        'estimated_wait_time': calculate_wait_time(
                            int(ride_info.get('current_waiting_riders', 0)),
                            int(ride_info.get('capacity_per_ride', 0)),
                            int(ride_info.get('ride_duration', 0))
                        )
                    }
                    all_rides_info.append(combined_info)
        
        # AI에 모든 시설 정보를 한 번에 전송하고 응답 받기
        if all_rides_info:
            decisions = await send_ai_prompt(all_rides_info)
            if decisions and len(decisions) == len(all_rides_info):
                # 각 시설에 대한 결정을 동시에 처리
                tasks = []
                for ride_info, decision in zip(all_rides_info, decisions):
                    tasks.append(parse_and_send_request(decision, ride_info['id']))
                await asyncio.gather(*tasks)
        
        await asyncio.sleep(5)

async def parse_and_send_request(ai_response, ride_id):
    """작업 실행 함수 업데이트"""
    async with httpx.AsyncClient() as client:
        try:
            if "1" in ai_response:
                print(f"[실행] 놀이기구 {ride_id} - 탑승 시작")
                response = await client.post(f"{REDIS_SERVICE_URL}/riders/start-ride/{ride_id}")
                print(f"[응답] 탑승 시작 - 상태 코드: {response.status_code}")
            elif "2" in ai_response:
                print(f"[실행] 놀이기구 {ride_id} - 하차 진행")
                response = await client.post(f"{REDIS_SERVICE_URL}/riders/complete-ride/{ride_id}")
                print(f"[응답] 하차 완료 - 상태 코드: {response.status_code}")
            else:
                print(f"[실행] 놀이기구 {ride_id} - 작업 없음")
        except httpx.HTTPError as exc:
            print(f"[오류] 놀이기구 {ride_id} 작업 실패: {exc}")

async def get_active_facilities():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FACILITY_SERVICE_URL}/facilities/active", headers=FACILITY_HEADERS)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "success" and data.get("data") and isinstance(data["data"].get("facilities"), list):
                facilities_data = data["data"]["facilities"]
                state = {}
                # Map the facilities to the desired format
                state['FACILITIES'] = [
                    {
                        'id': f['_id'],
                        'capacity': f['capacity_per_ride'],
                        'duration': f['ride_duration'],
                        'max_capacity': f['max_queue_capacity']
                    } for f in facilities_data
                ]
                print(f"초기화 완료: {len(state['FACILITIES'])}개 시설 로드됨")
                return state['FACILITIES']
            else:
                print("Unexpected data format from facilities service")
                return []
        except (httpx.HTTPError, KeyError) as exc:
            print(f"Failed to get active facilities: {exc}")
            return []

async def analyze_decision(ride_info, decision):
    """AI의 결정에 대한 분석 로그를 생성"""
    analysis = f"\n[결정 분석] {ride_info['name']}\n"
    analysis += f"현재 상태:\n"
    analysis += f"- 대기열: {ride_info['queue_length']}명\n"
    analysis += f"- 탑승 중: {ride_info['active_riders']}명\n"
    analysis += f"- 최대 수용: {ride_info['max_capacity']}명\n"
    analysis += f"- 예상 대기 시간: {ride_info['estimated_wait_time']}분\n"
    
    if decision == "1":
        analysis += "결정: 탑승 시작\n"
        if ride_info['queue_length'] > 0:
            analysis += "근거: 대기열에 손님이 있어 탑승을 시작합니다.\n"
        else:
            analysis += "경고: 대기열이 비어있는데 탑승 시작을 선택했습니다.\n"
    elif decision == "2":
        analysis += "결정: 하차 진행\n"
        if ride_info['active_riders'] > 0:
            analysis += "근거: 현재 탑승 중인 손님의 하차가 필요합니다.\n"
        else:
            analysis += "경고: 탑승 중인 손님이 없는데 하차를 선택했습니다.\n"
    elif decision == "3":
        analysis += "결정: 대기\n"
        if ride_info['queue_length'] == 0:
            analysis += "근거: 대기열이 비어있어 대기합니다.\n"
        elif ride_info['active_riders'] == ride_info['max_capacity']:
            analysis += "근거: 놀이기구가 최대 수용 인원에 도달했습니다.\n"
        else:
            analysis += "참고: 다른 조건으로 인한 대기 상태입니다.\n"
    
    print(analysis)
    return analysis

async def monitor_queues():
    while True:
        facilities = await get_active_facilities()
        all_rides_info = []
        
        print("\n[모니터링] 시설 상태 수집 시작")
        async with httpx.AsyncClient() as client:
            for facility in facilities:
                ride_info = await get_ride_info(facility['id'])
                if ride_info:
                    combined_info = {
                        'id': facility['id'],
                        'name': ride_info.get('facility_name', 'Unknown'),
                        'duration': ride_info.get('ride_duration', 0),
                        'max_capacity': int(ride_info.get('max_capacity', 0)),
                        'queue_length': int(ride_info.get('current_waiting_riders', 0)),
                        'active_riders': int(ride_info.get('current_active_riders', 0)),
                        'estimated_wait_time': calculate_wait_time(
                            int(ride_info.get('current_waiting_riders', 0)),
                            int(ride_info.get('capacity_per_ride', 0)),
                            int(ride_info.get('ride_duration', 0))
                        )
                    }
                    all_rides_info.append(combined_info)
        
        print(f"[모니터링] {len(all_rides_info)}개 시설 정보 수집 완료")
        
        if all_rides_info:
            decisions = await send_ai_prompt(all_rides_info)
            if decisions and len(decisions) == len(all_rides_info):
                print("\n[분석] AI 결정 분석 시작")
                tasks = []
                # 각 시설에 대한 결정을 분석하고 실행
                for ride_info, decision in zip(all_rides_info, decisions):
                    # 결정 분석 로그 생성
                    await analyze_decision(ride_info, decision)
                    # 결정된 작업 실행
                    tasks.append(parse_and_send_request(decision, ride_info['id']))
                
                print("\n[실행] 결정된 작업 실행 시작")
                await asyncio.gather(*tasks)
                print("[실행] 모든 작업 실행 완료")
            else:
                print("[오류] AI 응답이 시설 수와 일치하지 않습니다")
        
        print(f"\n[대기] {1}초 후 다음 모니터링 시작")
        await asyncio.sleep(1)

def calculate_wait_time(waiting_riders, capacity_per_ride, ride_duration):
    if capacity_per_ride == 0:
        return 0
    num_rides_needed = waiting_riders / capacity_per_ride
    return round(num_rides_needed * ride_duration)

def main():
    asyncio.run(monitor_queues())

if __name__ == "__main__":
    main()