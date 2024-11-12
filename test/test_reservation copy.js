import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

export const options = {
    vus: 1,
    iterations: 1
};

const BASE_URL = 'http://192.168.31.111/reservations/api';
const FACILITY_SERVICE_URL = 'https://parkservice.mintcocoa.cc/facilities/api';
let ACTIVE_FACILITIES = [];

export function setup() {
    console.log('시설 정보 조회 시작...');
    const facilitiesResponse = http.get(`${FACILITY_SERVICE_URL}/facilities/active`, {
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
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
                console.log('활성화된 시설 목록:', JSON.stringify(ACTIVE_FACILITIES, null, 2));
            }
        } catch (error) {
            console.error('시설 데이터 파싱 실패:', error.message);
        }
    }

    if (ACTIVE_FACILITIES.length === 0) {
        throw new Error('활성화된 시설을 찾을 수 없습니다');
    }

    return { ACTIVE_FACILITIES };
}

export default function (data) {
    const userId = `user_${randomString(8)}`;
    const facility = data.ACTIVE_FACILITIES[0];  // 첫 번째 시설 선택
    
    console.log(`테스트 시작 - 시설: ${facility.name} (${facility.id}), 사용자: ${userId}`);

    // 1. 예약 생성
    const reservationData = {
        user_id: userId,
        number_of_people: 2,
        reservation_time: new Date().toISOString()
    };

    console.log('예약 요청 데이터:', JSON.stringify(reservationData, null, 2));

    const reserveResponse = http.post(
        `${BASE_URL}/reserve/${facility.id}`,
        JSON.stringify(reservationData),
        {
            headers: { 'Content-Type': 'application/json' }