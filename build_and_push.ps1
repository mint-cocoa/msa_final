# PowerShell script for building and pushing Docker images

Write-Host "Starting build and push process..." -ForegroundColor Green

# External Services
$services = @(
    @{name="parkservice"; path="./external-services/park_service"},
    @{name="facilityservice"; path="./external-services/facility_service"},
    @{name="userservice"; path="./external-services/user_service"},
    @{name="ticketservice"; path="./external-services/ticket_service"},
    @{name="structuremanager"; path="./external-services/structure_manager"}
)

# Internal Services
$internal_services = @(
    @{name="ridereservationservice"; path="./internal_services/ride_reservation_service"},
    @{name="notificationservice"; path="./internal_services/notification_service"},
    @{name="realtimetrackingservice"; path="./internal_services/real_time_tracking_service"},
    @{name="redisservice"; path="./internal_services/redis_service"}
)

# Combine all services
$all_services = $services + $internal_services

foreach ($service in $all_services) {
    Write-Host "Building and pushing msa-$($service.name)..." -ForegroundColor Cyan
    
    # Check if directory exists
    if (-not (Test-Path $service.path)) {
        Write-Host "Warning: Directory $($service.path) not found, skipping..." -ForegroundColor Yellow
        continue
    }
    
    try {
        # Build and push with platform specifications
        docker buildx build `
            --platform linux/amd64,linux/arm64 `
            -t "kasd0134/msa-$($service.name):latest" `
            $service.path `
            --push

        if ($LASTEXITCODE -eq 0) {
            Write-Host "Successfully built and pushed msa-$($service.name)" -ForegroundColor Green
        } else {
            Write-Host "Failed to build and push msa-$($service.name)" -ForegroundColor Red
            exit 1
        }
    }
    catch {
        Write-Host "Error occurred while building msa-$($service.name): $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host "All services have been built and pushed successfully!" -ForegroundColor Green 