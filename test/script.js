import http from 'k6/http';
import { check, sleep } from 'k6';
import { randomString } from 'https://jslib.k6.io/k6-utils/1.2.0/index.js';

const BASE_URL_USERS = 'http://192.168.31.111/users';
const BASE_URL_PARKS = 'http://192.168.31.111/parks';
const BASE_URL_FACILITIES = 'http://192.168.31.111/facilities';

// 관리자 계정 생성 및 로그인을 위한 설정
const ADMIN_EMAIL = 'admin@test.com';
const ADMIN_PASSWORD = 'admin1234';

export const options = {
  vus: 1,  // 순차적으로 생성하기 위해 1로 설정
  iterations: 1
};

// 시설 타입 목록
const FACILITY_TYPES = [
  { name: 'Roller Coaster', max_capacity: 100 },
  { name: 'Water Slide', max_capacity: 75 },
  { name: 'Ferris Wheel', max_capacity: 50 },
  { name: 'Carousel', max_capacity: 40 },
  { name: 'Haunted House', max_capacity: 30 },
  { name: 'Bumper Cars', max_capacity: 45 },
  { name: 'Log Flume', max_capacity: 60 },
  { name: 'Swing Ride', max_capacity: 35 },
  { name: 'Drop Tower', max_capacity: 40 },
  { name: 'Virtual Reality Experience', max_capacity: 25 }
];

// 공원 테마 목록
const PARK_THEMES = [
  'Adventure World',
  'Fantasy Kingdom',
  'Ocean Paradise',
  'Space Station',
  'Dinosaur Park',
  'Magic Land',
  'Wild West Town',
  'Future World',
  'Fairy Tale Village',
  'Animal Safari'
];

export function setup() {
  console.log('1단계: 관리자 계정 생성 시작');
  const adminCreateResponse = http.post(`${BASE_URL_USERS}/api/`, JSON.stringify({
    email: ADMIN_EMAIL,
    password: ADMIN_PASSWORD,
    is_admin: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }), {
    headers: { 'Content-Type': 'application/json' }
  });

  check(adminCreateResponse, {
    '관리자 계정 생성 성공': (r) => r.status === 200,
  });
  console.log('관리자 계정 생성 완료');

  console.log('2단계: 관리자 로그인 시작');
  const loginResponse = http.post(`${BASE_URL_USERS}/api/login`, {
    username: ADMIN_EMAIL,
    password: ADMIN_PASSWORD,
    grant_type: 'password',
    scope: '',
    client_id: null,
    client_secret: null
  });

  check(loginResponse, {
    '관리자 로그인 성공': (r) => r.status === 200,
  });
  console.log('관리자 로그인 완료');

  return { authToken: loginResponse.json('access_token') };
}

export default function (data) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${data.authToken}`
  };

  console.log('3단계: 공원 및 시설 생성 시작');
  PARK_THEMES.forEach((theme, index) => {
    console.log(`공원 생성 시작: ${theme}`);
    const numFacilities = Math.floor(Math.random() * 6) + 5;
    const facilities = [];
    
    for (let i = 0; i < numFacilities; i++) {
      const facilityType = FACILITY_TYPES[Math.floor(Math.random() * FACILITY_TYPES.length)];
      console.log(`시설 생성 시작: ${facilityType.name}`);
      const facilityResponse = http.post(
        `${BASE_URL_FACILITIES}/api/`,
        JSON.stringify({
          name: `${facilityType.name}_${randomString(5)}`,
          description: `A ${facilityType.name.toLowerCase()} attraction`,
          is_operating: true,
          open_time: '2024-10-24T09:00:00',
          close_time: '2024-10-24T18:00:00',
          max_queue_capacity: facilityType.max_capacity
        }),
        { headers }
      );
      
      check(facilityResponse, {
        '시설 생성 성공': (r) => r.status === 200,
      });
      
      facilities.push(facilityResponse.json('_id'));
      console.log(`시설 생성 완료: ${facilityType.name}`);
      sleep(1);
    }

    const parkResponse = http.post(
      `${BASE_URL_PARKS}/api/`,
      JSON.stringify({
        name: theme,
        location: `Location ${index + 1}`,
        description: `A themed park featuring ${theme.toLowerCase()} attractions`,
        ticket_types: [
          {
            name: 'General Admission',
            description: 'Basic entry ticket',
            price: 50.0,
            allowed_facilities: facilities
          },
          {
            name: 'VIP Pass',
            description: 'Premium access to all attractions',
            price: 100.0,
            allowed_facilities: facilities
          }
        ]
      }),
      { headers }
    );

    check(parkResponse, {
      '공원 생성 성공': (r) => r.status === 200,
    });
    console.log(`공원 생성 완료: ${theme}`);

    sleep(1);
  });
  console.log('모든 공원 및 시설 생성 완료');
}
