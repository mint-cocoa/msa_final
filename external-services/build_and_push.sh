#!/bin/bash

# 기본 디렉토리 설정 (external-services 디렉토리의 절대 경로로 변경해야 함)
BASE_DIR="/Users/cocoa/Documents/GitHub/msa_final/external-services"

# Docker Hub 사용자 이름
DOCKER_USERNAME="kasd0134"

# 서비스 목록
SERVICES=("userservice" "parkservice" "facilityservice" "ticketservice" )
DIRECTORIES=("user-service" "park-service" "facility-service" "ticket-service" )

# 현재 날짜를 태그로 사용
TAG="latest"

# 각 서비스에 대해 반복
for i in "${!SERVICES[@]}"
do
    SERVICE=${SERVICES[$i]}
    DIRECTORY=${DIRECTORIES[$i]}
    
    echo "Building and pushing $SERVICE..."
    
    # 절대 경로를 사용하여 디렉토리로 이동
    cd "$BASE_DIR/$DIRECTORY"
    
    # Docker 이미지 빌드
    docker build -t "$DOCKER_USERNAME/msa-$SERVICE:$TAG" .
    
    # Docker Hub에 푸시
    docker push "$DOCKER_USERNAME/msa-$SERVICE:$TAG"
    
    echo "$SERVICE has been built and pushed successfully."
    echo "-------------------------------------------"
done

echo "All services have been built and pushed to Docker Hub."
