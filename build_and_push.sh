#!/bin/bash

# Set error handling
set -e

echo "Starting build and push process..."

# External Services
echo "Building and pushing external services..."

services=(
    "parkservice:./external-services/park_service"
    "facilityservice:./external-services/facility_service"
    "userservice:./external-services/user_service"
    "ticketservice:./external-services/ticket_service"
    "structuremanager:./external-services/structure_manager"
)

# Internal Services
echo "Building and pushing internal services..."

internal_services=(
    "ridereservationservice:./internal_services/ride_reservation_service"
    "notificationservice:./internal_services/notification_service"
    "realtimetrackingservice:./internal_services/real_time_tracking_service"
    "redisservice:./internal_services/redis_service"
)

# Build and push all services
for service in "${services[@]}" "${internal_services[@]}"; do
    IFS=: read -r name path <<< "${service}"
    echo "Building and pushing msa-${name}..."
    
    # Check if directory exists
    if [ ! -d "$path" ]; then
        echo "Warning: Directory $path not found, skipping..."
        continue
    }
    
    # Build and push with platform specifications
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        -t "kasd0134/msa-${name}:latest" \
        "${path}" \
        --push
    
    if [ $? -eq 0 ]; then
        echo "Successfully built and pushed msa-${name}"
    else
        echo "Failed to build and push msa-${name}"
        exit 1
    fi
done

echo "All services have been built and pushed successfully!"
