import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
    scenarios: {
        reservation_flow: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '1m', target: 100 },
                { duration: '2m', target: 100 },
                { duration: '1m', target: 0 },
            ],
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<500'],
        http_req_failed: ['rate<0.1'],
    },
};

const BASE_URL = 'http://192.168.31.111/reservations/api';
const FACILITY_SERVICE_URL = 'http://192.168.31.111/facilities/api';
let ACTIVE_FACILITIES = [];

export function setup() {
    console.log('시설 정보 조회 시작...');
    const facilitiesResponse = http.get(`${FACILITY_SERVICE_URL}/facilities/active`, {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    });

    check(facilitiesResponse, {
        '시설 조회 응답 성공': (r) => r.status === 200,
        '응답 본문 존재': (r) => r.body.length > 0
    });

    console.log('응답 상태 코드:', facilitiesResponse.status);
    console.log('응답 본문:', facilitiesResponse.body);

    if (facilitiesResponse.status === 200) {
        try {
            const data = JSON.parse(facilitiesResponse.body);
            console.log('파싱된 데이터:', JSON.stringify(data, null, 2));

            if (data.status === "success" && data.data && Array.isArray(data.data.facilities)) {
                ACTIVE_FACILITIES = data.data.facilities.map(f => ({
                    id: f._id,
                    name: f.name,
                    capacity: f.capacity_per_ride,
                    duration: f.ride_duration,
                    max_capacity: f.max_queue_capacity
                }));
                console.log(`활성화된 시설 수: ${ACTIVE_FACILITIES.length}`);
                console.log('시설 목록:', JSON.stringify(ACTIVE_FACILITIES, null, 2));
            } else {
                console.error('올바른 시설 데이터 형식이 아닙니다:', data);
            }
        } catch (error) {
            console.error('시설 데이터 파싱 실패:', error.message);
            console.error('응답 본문:', facilitiesResponse.body);
        }
    } else {
        console.error('시설 조회 실패:', facilitiesResponse.status, facilitiesResponse.body);
    }

    return { ACTIVE_FACILITIES };
}

function getRandomFacility() {
    if (ACTIVE_FACILITIES.length === 0) {
        console.error('활성화된 시설이 없습니다');
        return null;
    }
    return ACTIVE_FACILITIES[Math.floor(Math.random() * ACTIVE_FACILITIES.length)];
}

export default function () {
    const userId = `user_${randomString(8)}`;
    const facility = getRandomFacility();
    
    if (!facility) {
        console.error('시설 정보를 가져올 수 없습니다');
        return;
    }

    const reservationData = {
        user_id: userId,
        number_of_people: Math.floor(Math.random() * 4) + 1,
        reservation_time: new Date().toISOString()
    };

    const reserveResponse = http.post(
        `${BASE_URL}/reserve/${facility.id}`,
        JSON.stringify(reservationData),
        {
            headers: { 'Content-Type': 'application/json' }
        }
    );

    check(reserveResponse, {
        '예약 생성 성공': (r) => r.status === 200,
        '대기열 위치 존재': (r) => r.json('queue_position') !== undefined,
        '예상 대기 시간 존재': (r) => r.json('estimated_wait_time') !== undefined
    });

    sleep(1);

    if (Math.random() < 0.2) {
        const queueStatusResponse = http.get(
            `${BASE_URL}/queue-status/${facility.id}?user_id=${userId}`
        );

        if (queueStatusResponse.status === 200) {
            try {
                const queueInfo = queueStatusResponse.json();
                console.log(`
                    ===== 대기열 상태 =====
                    시설명: ${facility.name}
                    시설 ID: ${facility.id}
                    사용자 ID: ${userId}
                    총 대기 인원: ${queueInfo.queue_length}명
                    탑승 정원: ${facility.capacity}명
                    소요 시간: ${facility.duration}분
                    현재 시간: ${new Date().toISOString()}
                    ====================
                `);
            } catch (error) {
                console.log('대기열 정보 파싱 실패:', error.message);
            }
        }
    }

    sleep(1);

    if (Math.random() < 0.3) {
        const cancelData = {
            reason: "테스트 예약 취소"
        };

        const cancelResponse = http.post(
            `${BASE_URL}/cancel/${facility.id}?user_id=${userId}`,
            JSON.stringify(cancelData),
            {
                headers: { 'Content-Type': 'application/json' }
            }
        );

        check(cancelResponse, {
            '예약 취소 성공': (r) => r.status === 200
        });
    }

    sleep(2);
}