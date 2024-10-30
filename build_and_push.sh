#!/bin/bash

# External Services
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-parkservice:latest ./external-services/park_service --push
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-facilityservice:latest ./external-services/facility_service --push
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-userservice:latest ./external-services/user_service --push
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-ticketservice:latest ./external-services/ticket_service --push
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-structuremanager:latest ./external-services/structure_manager --push

# Internal Services
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-ridereservationservice:latest ./internal_services/ride_reservation_service --push
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-notificationservice:latest ./internal_services/notification_service --push
docker buildx build --platform linux/amd64,linux/arm64 -t kasd0134/msa-realtimetrackingservice:latest ./internal_services/real_time_tracking_service --push