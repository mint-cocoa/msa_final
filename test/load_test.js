import http from 'k6/http';
import { check, group } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';



// 전역 상태 관리
const STATE = {
    FACILITIES: [],
    TIME_SETTINGS: {
        PARK_OPEN_HOUR: 9,
        PARK_CLOSE_HOUR: 22,
        currentTime: new Date(),
        
        // 시간 관리 메서드들
        initialize() {
            this.currentTime = new Date();
            this.currentTime.setHours(this.PARK_OPEN_HOUR, 0, 0, 0);
        },
        
        advance() {
            this.currentTime.setMinutes(this.currentTime.getMinutes() + 1);
            return this.currentTime;
        },
        
        getCurrentTime() {
            return this.currentTime || this.initialize();
        }
    },
};

// setup 함수 - 테스트 시작 전 1회 실행
export function setup() {
    // 시간 초기화
    STATE.TIME_SETTINGS.initialize();
    
    // 시설 정보 조회
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
                console.info(`초기화 완료: ${STATE.FACILITIES.length}개 시설 로드됨`);
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

export default function (data) {
    if (!data || !data.facilities || data.facilities.length === 0) {
        console.error('시설 데이터가 없습니다');
        return;
    }

    // 시간 진행
    const currentTime = STATE.TIME_SETTINGS.advance();
    const currentHour = currentTime.getHours();
    
    if (currentHour < STATE.TIME_SETTINGS.PARK_OPEN_HOUR || 
        currentHour >= STATE.TIME_SETTINGS.PARK_CLOSE_HOUR) {
        console.info(`운영 시간이 아닙니다. 현재 시각: ${currentTime.toLocaleTimeString()}`);
        return;
    }

    console.info(`현재 시각: ${currentTime.toLocaleTimeString()}`);
    
    // 랜덤하게 시설 선택
    const facility = data.facilities[Math.floor(Math.random() * data.facilities.length)];
    
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
        console.error(`대기열 상태 조회 실패 - 시설 ID: ${facility.id}`);
        return;
    }

    const status = JSON.parse(statusResponse.body);
    const currentWaitingRiders = status.current_waiting_riders
    const currentActiveRiders = status.current_active_riders
    const maxCapacity = status.max_capacity 
    if (status.status !== 'active') {
        console.warn(`시설 ${facility.name} 상태 비활성화`);
        return;
    }

    console.info(`시설 ${facility.name} 현재 대기열: ${currentWaitingRiders}/${maxCapacity}`);

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
    if (currentWaitingRiders > 0) {
        const targetQueue = Math.floor(maxCapacity * 0.7);  // 목표 대기열 70%
        const minRequiredRiders = facility.capacity_per_ride;  // 최소 필요 탑승 인원
        
        let shouldStartRide = true;
        
        // ... shouldStartRide 결정 로직 ...
    
        if (shouldStartRide) {
            // 대기열 상태에 따른 동적 운행 시간 조정
            let durationMultiplier;
            const queueRatio = currentWaitingRiders / maxCapacity;
            
            if (queueRatio >= 0.9) {
                // 대기열이 90% 이상일 때 - 빠른 처리
                durationMultiplier = 0.5;  // 운행 시간 50%로 단축
            } else if (queueRatio >= 0.7) {
                // 대기열이 70-90%일 때 - 약간 빠른 처리
                durationMultiplier = 0.7;  // 운행 시간 70%로 단축
            } else if (queueRatio >= 0.4) {
                // 대기열이 40-70%일 때 - 정상 운행
                durationMultiplier = 1.0;  // 기본 운행 시간
            } else {
                // 대기열이 40% 미만일 때 - 여유있게 운행
                durationMultiplier = 1.2;  // 운행 시간 20% 증가
            }
    
            const adjustedDuration = Math.max(1, Math.round(facility.duration * durationMultiplier));
            console.info(`현재 대기율: ${Math.round(queueRatio * 100)}%, 조정된 운행 시간: ${adjustedDuration}분 (기본: ${facility.duration}분)`);
    
            const startRideResponse = http.post(
                `${REDIS_SERVICE_URL}/riders/start-ride/${facility.id}`,
                null,
                { headers: { 'Content-Type': 'application/json' } }
            );
    
            check(startRideResponse, {
                '탑승 시작 요청 성공': (r) => r.status === 200
            });

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
                // 탑승 시작 시간 기록
                const rideStartTime = new Date(STATE.TIME_SETTINGS.currentTime);
                const rideDurationMinutes = facility.duration;
                const rideEndTime = new Date(rideStartTime);
                rideEndTime.setMinutes(rideStartTime.getMinutes() + rideDurationMinutes);
                
                console.info(`탑승 시작: ${rideStartTime.toLocaleTimeString()}`);
                console.info(`예상 종료: ${rideEndTime.toLocaleTimeString()}`);

                // 현재 시간이 종료 시간을 지났는지 확인
                if (STATE.TIME_SETTINGS.currentTime >= rideEndTime) {
                    const completeRideResponse = http.post(
                        `${REDIS_SERVICE_URL}/riders/complete-ride/${facility.id}`,
                        null,
                        { headers: { 'Accept': 'application/json' } }
                    );

                    check(completeRideResponse, {
                        '탑승 완료 요청 성공': (r) => r.status === 200
                    });
                    
                    console.info(`탑승 완료 처리 (소요시간: ${rideDurationMinutes}분)`);
                } else {
                    console.info(`탑승 진행 중... (남은 시간: ${Math.ceil((rideEndTime - STATE.TIME_SETTINGS.currentTime) / 1000 / 60)}분)`);
                }
            }
        }
    } 
    console.info(`시설 ${facility.name}이 현재 운행 중 (탑승: ${currentActiveRiders}명, 대기: ${currentWaitingRiders}명)`);
    console.info(`시설 ${facility.name}이 대기 중 (대기열: ${currentWaitingRiders}명)`);
}
}
