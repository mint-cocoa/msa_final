import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 10, // 가상 사용자 수
  duration: '30s', // 테스트 지속 시간
};

export default function () {
  const rideId = '1234'; // 테스트할 ride_id
  const userId = Math.floor(Math.random() * 1000); // 임의의 사용자 ID 생성
  const reserveUrl = `http://192.168.31.111/reservations/api/dev/reserve/${userId}`; // 예약 서비스 URL
    const queueStatusUrl = `http://192.168.31.111/reservations/api/dev/queue_status/${rideId}`; // 큐 상태 조회 URL

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  // 예약 요청
  const reserveRes = http.get(reserveUrl, params);
  check(reserveRes, {
    'reserve is status 200': (r) => r.status === 200,
  });

  // 큐 상태 조회 요청
  const queueStatusRes = http.get(queueStatusUrl, params);
  check(queueStatusRes, {
    'queue status is status 200': (r) => r.status === 200,
  });
  console.log('Queue Status:', queueStatusRes.body);

  sleep(1);
}
