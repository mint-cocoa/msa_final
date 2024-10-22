#!/bin/bash

# Docker Hub 사용자 이름
DOCKER_USERNAME="kasd0134"

# 서비스 목록
SERVICES=("user-service" "park-service" "facility-service" "ticket-service" )

# 현재 날짜를 태그로 사용
TAG="latest"

# 각 서비스에 대해 반복
for SERVICE in "${SERVICES[@]}"
do
    echo "Building and pushing $SERVICE..."
    
    # 디렉토리로 이동
    cd "$SERVICE"
    
    # Docker 이미지 빌드
    docker build -t "$DOCKER_USERNAME/msa-$SERVICE:$TAG" .
    docker tag "$DOCKER_USERNAME/msa-$SERVICE:$TAG" "$DOCKER_USERNAME/msa-$SERVICE:latest"
    
    # Docker Hub에 푸시
    docker push "$DOCKER_USERNAME/msa-$SERVICE:$TAG"
    docker push "$DOCKER_USERNAME/msa-$SERVICE:latest"
    
    # 상위 디렉토리로 이동
    cd ..
    
    echo "$SERVICE has been built and pushed successfully."
    echo "-------------------------------------------"
done

echo "All services have been built and pushed to Docker Hub."
