import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const BASE_URL_USERS = 'http://192.168.31.111/users';
const BASE_URL_PARKS = 'http://192.168.31.111/parks';
const BASE_URL_TICKETS = 'http://192.168.31.111/tickets';
const BASE_URL_RIDES = 'http://192.168.31.111/rides';
const BASE_URL_RESERVATIONS = 'http://192.168.31.111/reservations';
const BASE_URL_FACILITIES = 'http://192.168.31.111/facilities';

export const options = {
  stages: [
    { duration: '1m', target: 50 },    // 1분 동안 50명으로 증가
    { duration: '3m', target: 50 },    // 3분 동안 50명 유지
    { duration: '1m', target: 0 },     // 1분 동안 0명으로 감소
  ],
  thresholds: {
    http_req_duration: ['p(95)<2000'], // 95%의 요청이 2초 이내 완료
    http_req_failed: ['rate<0.05'],    // 실패율 5% 미만
  },
};

// SETUP: 50명의 사용자 생성 및 공원 입장
export function setup() {
  const users = [];
  const parksResponse = http.get(`${BASE_URL_PARKS}/api/`);
  const parks = JSON.parse(parksResponse.body);

  // 50명의 사용자 생성
  for (let i = 0; i < 50; i++) {
    const email = `user_${randomString(8)}@example.com`;
    const password = 'password123';

    // 회원가입
    const registerResponse = http.post(`${BASE_URL_USERS}/api/`, JSON.stringify({
      email: email,
      password: password,
      is_admin: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }), {
      headers: { 'Content-Type': 'application/json' }
    });

    // 로그인
    const loginResponse = http.post(`${BASE_URL_USERS}/api/login`, {
      username: email,
      password: password,
      grant_type: 'password',
      scope: '',
      client_id: null,
      client_secret: null
    });

    const authToken = loginResponse.json('access_token');
    const userId = registerResponse.json('_id');

    // 티켓 구매
    if (parks.length > 0) {
      const randomPark = parks[Math.floor(Math.random() * parks.length)];
      const randomTicketType = randomPark.ticket_types[Math.floor(Math.random() * randomPark.ticket_types.length)];

      const ticketPurchaseResponse = http.post(`${BASE_URL_TICKETS}/api/`, JSON.stringify({
        user_id: userId,
        park_id: randomPark._id,
        ticket_type_name: randomTicketType.name
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`
        }
      });

      const ticketId = ticketPurchaseResponse.json('ticket_id');

      // 티켓 사용
      const useTicketResponse = http.post(`${BASE_URL_TICKETS}/api/use/${ticketId}`, null, {
        headers: {
          'Authorization': `Bearer ${authToken}`
        }
      });

      const ticketToken = useTicketResponse.json('access_token');

      users.push({
        userId,
        authToken,
        ticketToken
      });
    }
    sleep(1); // 사용자 생성 간 간격
  }

  console.log(`생성된 사용자 수: ${users.length}`);
  return { users, parks };
}

// 메인 시나리오: 생성된 사용자들의 놀이기구 이용
export default function (data) {
  const user = data.users[Math.floor(Math.random() * data.users.length)];
  
  // 운영 중인 시설 목록 조회
  const facilitiesResponse = http.get(
    `${BASE_URL_FACILITIES}/api/operating/all`,
    {
      headers: {
        'accept': 'application/json'
      }
    }
  );

  if (facilitiesResponse.status === 200) {
    const facilities = facilitiesResponse.json();
    if (facilities.length > 0) {
      const randomFacility = facilities[Math.floor(Math.random() * facilities.length)];
      const rideId = randomFacility._id;

      // 놀이기구 예약
      const reserveRideResponse = http.post(
        `${BASE_URL_RESERVATIONS}/api/reserve/${rideId}`,
        null,
        {
          headers: {
            'Authorization': `Bearer ${user.ticketToken}`,
            'Content-Type': 'application/json'
          }
        }
      );

      check(reserveRideResponse, {
        '놀이기구 예약 성공': (r) => r.status === 200,
      });

      if (reserveRideResponse.status === 200) {
        // 대기열 위치 확인
        const queuePositionResponse = http.get(
          `${BASE_URL_RESERVATIONS}/api/queue_position/${rideId}`,
          {
            headers: {
              'Authorization': `Bearer ${user.ticketToken}`
            }
          }
        );

        check(queuePositionResponse, {
          '대기열 위치 조회 성공': (r) => r.status === 200,
        });
      }
    }
  }

  sleep(Math.random() * 2 + 1); // 1-3초 랜덤 대기
}
