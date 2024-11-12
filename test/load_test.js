import http from 'k6/http';
import { check, group } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

// 전역 상태 관리
const STATE = {
    FACILITIES: []
};

// setup 함수 - 테스트 시작 전 1회 실행
export function setup() {
    const facilitiesResponse = http.get(`${FACILITY_SERVICE_URL}/facilities/active`, {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    });

    if (facilitiesResponse.status === 200) {
        try {
            const data = JSON.parse(facilitiesResponse.body);
            if (data.status === "success" && data.data && Array.isArray(data.data.facilities)) {
                STATE.FACILITIES = data.data.facilities.map(f => ({
                    id: f._id,
                    name: f.name,
                    capacity: f.capacity_per_ride,
                    duration: f.ride_duration,
                    max_capacity: f.max_queue_capacity
                }));
                
                // 각 시설 초기화
                console.info('시설 초기화 시작...');
                STATE.FACILITIES.forEach(facility => {
                    const resetResponse = http.post(
                        `${REDIS_SERVICE_URL}/facility/reset/${facility.id}`,
                        null,
                        {
                            headers: {
                                'Accept': 'application/json',
                                'Content-Type': 'application/json'
                            }
                        }
                    );
                    
                    if (resetResponse.status === 200) {
                        console.info(`시설 초기화 완료: ${facility.name} (${facility.id})`);
                    } else {
                        console.error(`시설 초기화 실패: ${facility.name} (${facility.id}) - 상태 코드: ${resetResponse.status}`);
                    }
                });

                console.info(`초기화 완료: ${STATE.FACILITIES.length}개 시설 로드 및 초기화됨`);
                return { facilities: STATE.FACILITIES };
            }
        } catch (error) {
            console.error('시설 데이터 초기화 실패:', error.message);
            return null;
        }
    }
    return null;
}

export const options = {
    scenarios: {
        reservation_flow: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '1m', target: 30 },
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<500', 'p(99)<1000'],
        http_req_failed: ['rate<0.05'],
    },
};

const BASE_URL = 'https://parkservice.mintcocoa.cc/reservations/api';
const REDIS_SERVICE_URL = 'https://parkservice.mintcocoa.cc/redis/api';
const FACILITY_SERVICE_URL = 'https://parkservice.mintcocoa.cc/facilities/api';

export default function (data) {
    if (!data || !data.facilities || data.facilities.length === 0) {
        console.error('시설 데이터가 없습니다');
        return;
    }

    // 시설 번호 기반 선택 (1부터 시설 수까지의 숫자 중 하나 선택)
    const facilityIndex = Math.floor(Math.random() * data.facilities.length);
    const facility = data.facilities[facilityIndex];
    console.info(`선택된 시설: ${facility.name} (${facilityIndex + 1}번)`);
    
    // 1. 시설 대기열 정보 조회
    const statusResponse = http.get(`${REDIS_SERVICE_URL}/ride_info/${facility.id}`, {
        headers: { 'Accept': 'application/json' }
    });

    const statusCheck = check(statusResponse, {
        '대기열 상태 조회 성공': (r) => r.status === 200,
        '대기열 데이터 유효성 확인': (r) => {
            try {
                const body = JSON.parse(r.body);
                return body.facility_name !== undefined &&
                       body.current_waiting_riders !== undefined &&
                       body.current_active_riders !== undefined;
            } catch (e) {
                return false;
            }
        }
    });

    if (!statusCheck) {
        console.error(`대기열 상태 조회 실패 - 시설 ID: ${facility.id}`);
        return;
    }

    const status = JSON.parse(statusResponse.body);
    const currentWaitingRiders = parseInt(status.current_waiting_riders);
    const currentActiveRiders = parseInt(status.current_active_riders);
    const maxCapacity = parseInt(status.max_capacity);

    console.info(`시설 ${facility.name} 현재 대기자 : ${currentWaitingRiders}`);
    console.info(`시설 ${facility.name} 현재 탑승자 : ${currentActiveRiders}`);
    console.info(`시설 ${facility.name} 최대 수용 인원 : ${maxCapacity}`);
    if (status.status !== 'active') {
        console.warn(`시설 ${facility.name} 상태 비활성화`);
        return;
    }
    
    const numberOfPeople = Math.floor(Math.random() * 4) + 1;
    const reservation_time = new Date().toISOString();
    const user_id = `user_${randomString(8)}`;

    const reserveResponse = http.post(
        `${BASE_URL}/reserve/${facility.id}`,
        JSON.stringify({ number_of_people: numberOfPeople, user_id: user_id, reservation_time: reservation_time }),
        { headers: { 'Content-Type': 'application/json' } }
    );

    check(reserveResponse, {
        '예약 요청 성공': (r) => r.status === 200
    });

}
