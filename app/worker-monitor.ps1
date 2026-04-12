# AstroNova Celery Worker Monitoring Script (PowerShell)
# Usage: .\worker-monitor.ps1 [status|logs|restart|inspect]

param(
    [Parameter(Position=0)]
    [ValidateSet("status", "stat", "logs", "log", "restart", "inspect", "info", "queue", "q", "clear", "help")]
    [string]$Command = "status"
)

$ContainerName = "astronova_celery"
$WorkerName = "celery@astronova_celery"

switch ($Command) {
    { $_ -in "status", "stat" } {
        Write-Host "Checking worker status..." -ForegroundColor Cyan
        Write-Host "================================" -ForegroundColor Cyan
        
        # Check if container is running
        $containerRunning = docker ps -q -f name=$ContainerName 2>$null
        if ($containerRunning) {
            Write-Host "Container: $ContainerName is running" -ForegroundColor Green
            
            # Check worker ping
            Write-Host ""
            Write-Host "Worker connectivity:" -ForegroundColor Yellow
            try {
                docker exec $ContainerName celery -A services.pdf_tasks inspect ping -d $WorkerName 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "Worker responding to ping" -ForegroundColor Green
                } else {
                    Write-Host "Worker not responding to ping" -ForegroundColor Red
                }
            } catch {
                Write-Host "Worker not responding to ping" -ForegroundColor Red
            }
            
            # Show active tasks
            Write-Host ""
            Write-Host "Active tasks:" -ForegroundColor Yellow
            try {
                $activeTasks = docker exec $ContainerName celery -A services.pdf_tasks inspect active -d $WorkerName 2>$null
                if ($activeTasks -and $LASTEXITCODE -eq 0) {
                    Write-Host $activeTasks
                } else {
                    Write-Host "No active tasks" -ForegroundColor Gray
                }
            } catch {
                Write-Host "No active tasks" -ForegroundColor Gray
            }
            
            # Show resource usage
            Write-Host ""
            Write-Host "Resource usage:" -ForegroundColor Yellow
            try {
                docker stats $ContainerName --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>$null
            } catch {
                Write-Host "Cannot get stats" -ForegroundColor Red
            }
            
        } else {
            Write-Host "Container: $ContainerName is not running" -ForegroundColor Red
            Write-Host ""
            Write-Host "To start: docker-compose up -d celery_worker" -ForegroundColor Yellow
        }
        break
    }
    
    { $_ -in "logs", "log" } {
        Write-Host "Worker logs (last 50 lines):" -ForegroundColor Cyan
        Write-Host "=================================" -ForegroundColor Cyan
        docker logs --tail=50 -f $ContainerName
        break
    }
    
    "restart" {
        Write-Host "Restarting worker..." -ForegroundColor Yellow
        docker-compose restart celery_worker
        Write-Host "Worker restarted" -ForegroundColor Green
        break
    }
    
    { $_ -in "inspect", "info" } {
        Write-Host "Detailed worker inspection:" -ForegroundColor Cyan
        Write-Host "==============================" -ForegroundColor Cyan
        
        $containerRunning = docker ps -q -f name=$ContainerName 2>$null
        if ($containerRunning) {
            Write-Host "Worker statistics:" -ForegroundColor Yellow
            docker exec $ContainerName celery -A services.pdf_tasks inspect stats -d $WorkerName
            
            Write-Host ""
            Write-Host "Worker configuration:" -ForegroundColor Yellow
            docker exec $ContainerName celery -A services.pdf_tasks inspect conf -d $WorkerName
            
            Write-Host ""
            Write-Host "Registered tasks:" -ForegroundColor Yellow
            docker exec $ContainerName celery -A services.pdf_tasks inspect registered -d $WorkerName
        } else {
            Write-Host "Worker container not running" -ForegroundColor Red
        }
        break
    }
    
    { $_ -in "queue", "q" } {
        Write-Host "Queue inspection:" -ForegroundColor Cyan
        Write-Host "===================" -ForegroundColor Cyan
        
        # Check Redis queue lengths
        Write-Host "Queue lengths:" -ForegroundColor Yellow
        try {
            $queueLength = docker exec astronova_redis redis-cli llen pdf 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "PDF queue: $queueLength tasks" -ForegroundColor White
            } else {
                Write-Host "Cannot connect to Redis" -ForegroundColor Red
            }
        } catch {
            Write-Host "Cannot connect to Redis" -ForegroundColor Red
        }
        
        # Check scheduled tasks
        Write-Host ""
        Write-Host "Scheduled tasks:" -ForegroundColor Yellow
        try {
            $scheduledTasks = docker exec $ContainerName celery -A services.pdf_tasks inspect scheduled -d $WorkerName 2>$null
            if ($scheduledTasks -and $LASTEXITCODE -eq 0) {
                Write-Host $scheduledTasks
            } else {
                Write-Host "No scheduled tasks" -ForegroundColor Gray
            }
        } catch {
            Write-Host "No scheduled tasks" -ForegroundColor Gray
        }
        break
    }
    
    "clear" {
        Write-Host "Clearing failed tasks from Redis..." -ForegroundColor Yellow
        docker exec astronova_redis redis-cli flushdb
        Write-Host "Redis queues cleared" -ForegroundColor Green
        break
    }
    
    "help" {
        Write-Host "AstroNova Celery Worker Monitor" -ForegroundColor Cyan
        Write-Host "===============================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Usage: .\worker-monitor.ps1 [command]" -ForegroundColor White
        Write-Host ""
        Write-Host "Commands:" -ForegroundColor Yellow
        Write-Host "  status    - Show worker status and active tasks (default)" -ForegroundColor White
        Write-Host "  logs      - Show worker logs (follow mode)" -ForegroundColor White
        Write-Host "  restart   - Restart the worker container" -ForegroundColor White
        Write-Host "  inspect   - Detailed worker inspection" -ForegroundColor White
        Write-Host "  queue     - Check queue status and scheduled tasks" -ForegroundColor White
        Write-Host "  clear     - Clear failed tasks from Redis" -ForegroundColor White
        Write-Host "  help      - Show this help message" -ForegroundColor White
        Write-Host ""
        Write-Host "Examples:" -ForegroundColor Yellow
        Write-Host "  .\worker-monitor.ps1 status" -ForegroundColor Gray
        Write-Host "  .\worker-monitor.ps1 logs" -ForegroundColor Gray
        Write-Host "  .\worker-monitor.ps1 restart" -ForegroundColor Gray
        break
    }
}