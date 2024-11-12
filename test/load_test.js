import http from 'k6/http';
import { check, group } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';
import exec from 'k6/execution';

const log = {
    info: msg => { console.log(`INFO [${new Date().toISOString()}] ${msg}`) },
    warn: msg => { console.log(`WARN [${new Date().toISOString()}] ${msg}`) },
    error: msg => { console.log(`ERROR [${new Date().toISOString()}] ${msg}`) }
};

export const options = {
    scenarios: {
        reservation_flow: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '1m', target: 10 },    // 1분 동안 50명으로 증가
                { duration: '3m', target: 50 },    // 3분 동안 50명 유지
                { duration: '1m', target: 0 },     // 1분 동안 0명으로 감소
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

export default function () {
    // 시설 정보 조회
    const facilitiesResponse = http.get(`${FACILITY_SERVICE_URL}/facilities/active`, {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    });

    check(facilitiesResponse, {
        '시설 정보 조회 성공': (r) => r.status === 200
    });

    if (facilitiesResponse.status !== 200) {
        log.error('시설 조회 실패:', facilitiesResponse.status);
        return;
    }

    let facilities = [];
    try {
        const data = JSON.parse(facilitiesResponse.body);
        if (data.status === "success" && data.data && Array.isArray(data.data.facilities)) {
            facilities = data.data.facilities.map(f => ({
                id: f._id,
                name: f.name,
                capacity: f.capacity_per_ride,
                duration: f.ride_duration,
                max_capacity: f.max_queue_capacity
            }));
            log.info(`활성화된 시설 수: ${facilities.length}`);
        } else {
            log.error('올바른 시설 데이터 형식이 아닙니다');
            return;
        }
    } catch (error) {
        log.error('시설 데이터 파싱 실패:', error.message);
        return;
    }

    if (facilities.length === 0) {
        log.error('활성화된 시설이 없습니다');
        return;
    }

    // 랜덤하게 하나의 시설 선택
    const facility = facilities[Math.floor(Math.random() * facilities.length)];
    
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
                body.max_capacity !== undefined &&
                body.ride_duration !== undefined &&
                body.capacity_per_ride !== undefined &&
                body.status !== undefined &&
                body.current_waiting_riders !== undefined &&
                body.current_active_riders !== undefined; 
            } catch (e) {
                return false;
            }
        }
    });

    if (!statusCheck) {
        log.error(`대기열 상태 조회 실패 - 시설 ID: ${facility.id}`);
        return;
    }

    const status = JSON.parse(statusResponse.body);
    const currentWaitingRiders = status.current_waiting_riders
    const currentActiveRiders = status.current_active_riders
    const maxCapacity = parseInt(status.max_capacity, 10);

    if (status.status !== 'active') {
        log.warn(`시설 ${facility.name} 상태 비활성화`);
        return;
    }

    log.info(`시설 ${facility.name} 현재 대기열: ${currentWaitingRiders}/${maxCapacity}`);

    if (currentWaitingRiders < maxCapacity) {
        // 2. 예약 생성
        const numberOfPeople = Math.floor(Math.random() * 4) + 1;
        const userId = `user_${randomString(8)}`;
        const reservationData = {
            number_of_people: numberOfPeople,
            reservation_time: new Date().toISOString(),
            user_id: userId
        };

        const reserveResponse = http.post(
            `${BASE_URL}/reserve/${facility.id}`,
            JSON.stringify(reservationData),
            { headers: { 'Content-Type': 'application/json' } }
        );

        check(reserveResponse, {
            '예약 요청 성공': (r) => r.status === 200,
            '예약 요청 큐잉 확인': (r) => {
                try {
                    const body = JSON.parse(r.body);
                    return body.status === 'queued' && 
                           body.user_id === userId;
                } catch (e) {
                    return false;
                }
            }
        });

    }

    // 4. 놀이기구 운영 로직
    if (currentActiveRiders === 0 && currentWaitingRiders > 0) {
        const targetQueue = Math.floor(maxCapacity * 0.7);  // 목표 대기열 70%
        const minRequiredRiders = facility.capacity;  // 최소 필요 탑승 인원
        
        let shouldStartRide = true;
        
        if (currentWaitingRiders < minRequiredRiders) {
            shouldStartRide = false;
            log.info(`대기 인원 부족: ${currentWaitingRiders}명 (필요: ${minRequiredRiders}명) - 탑승 보류`);
        }
        else if (currentWaitingRiders >= minRequiredRiders) {
            const queueRatio = currentWaitingRiders / targetQueue;  // 현재 대기율
            let probability;
            
            if (queueRatio < 0.3) {
                // 대기열이 매우 적을 때 (30% 미만)
                probability = 0.2;  // 20% 확률로 운행
                log.info(`대기열 매우 부족 (${Math.round(queueRatio * 100)}%): ${currentWaitingRiders}명`);
            } 
            else if (queueRatio < 0.5) {
                // 대기열이 적을 때 (30-50%)
                probability = 0.4;  // 40% 확률로 운행
                log.info(`대기열 부족 (${Math.round(queueRatio * 100)}%): ${currentWaitingRiders}명`);
            }
            else if (queueRatio < 0.8) {
                // 대기열이 적정 수준일 때 (50-80%)
                probability = 0.6;  // 60% 확률로 운행
                log.info(`대기열 적정 (${Math.round(queueRatio * 100)}%): ${currentWaitingRiders}명`);
            }
            else if (queueRatio < 1.0) {
                // 대기열이 많을 때 (80-100%)
                probability = 0.8;  // 80% 확률로 운행
                log.info(`대기열 많음 (${Math.round(queueRatio * 100)}%): ${currentWaitingRiders}명`);
            }
            else {
                // 대기열이 가득 찼을 때 (100% 이상)
                probability = 1.0;  // 100% 확률로 운행
                log.info(`대기열 포화 (${Math.round(queueRatio * 100)}%): ${currentWaitingRiders}명`);
            }
            
            shouldStartRide = Math.random() < probability;
            
            // 운행 결정 로그
            const decisionMsg = shouldStartRide ? '실행' : '보류';
            const probabilityPercent = Math.round(probability * 100);
            log.info(`탑승 처리 결정 (${probabilityPercent}% 확률): ${decisionMsg}`);
            
            // 대기 시간 예상 계산
            const estimatedCycles = Math.ceil(currentWaitingRiders / facility.capacity);
            const estimatedWaitTime = estimatedCycles * facility.duration;
            log.info(`예상 대기 시간: 약 ${estimatedWaitTime}분 (${estimatedCycles}회 운행 필요)`);
        }

        if (shouldStartRide) {
            const startRideResponse = http.post(
                `${REDIS_SERVICE_URL}/riders/start-ride/${facility.id}`,
                null,
                { headers: { 'Content-Type': 'application/json' } }
            );

            check(startRideResponse, {
                '탑승 시작 요청 성공': (r) => r.status === 200
            });

            if (startRideResponse.status === 200) {
                const completeRideResponse = http.post(
                    `${REDIS_SERVICE_URL}/riders/complete-ride/${facility.id}`,
                    null,
                    { headers: { 'Accept': 'application/json' } }
                );

                check(completeRideResponse, {
                    '탑승 완료 요청 성공': (r) => r.status === 200
                });
            }
        }
    } 


    log.info(`시설 ${facility.name}이 현재 운행 중 (탑승: ${currentActiveRiders}명, 대기: ${currentWaitingRiders}명)`);
    log.info(`시설 ${facility.name}이 대기 중 (대기열: ${currentWaitingRiders}명)`);
    
}


