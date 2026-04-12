#!/bin/bash

# AstroNova Celery Worker Monitoring Script
# Usage: ./worker-monitor.sh [status|logs|restart|inspect]

CONTAINER_NAME="astronova_celery"
WORKER_NAME="celery@astronova_celery"

case "${1:-status}" in
    "status"|"stat")
        echo "🔍 Checking worker status..."
        echo "================================"
        
        # Check if container is running
        if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
            echo "✅ Container: $CONTAINER_NAME is running"
            
            # Check worker ping
            echo ""
            echo "📡 Worker connectivity:"
            docker exec $CONTAINER_NAME celery -A services.pdf_tasks inspect ping -d $WORKER_NAME 2>/dev/null || echo "❌ Worker not responding to ping"
            
            # Show active tasks
            echo ""
            echo "🔄 Active tasks:"
            docker exec $CONTAINER_NAME celery -A services.pdf_tasks inspect active -d $WORKER_NAME 2>/dev/null || echo "ℹ️  No active tasks"
            
            # Show resource usage
            echo ""
            echo "📊 Resource usage:"
            docker stats $CONTAINER_NAME --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" 2>/dev/null || echo "❌ Cannot get stats"
            
        else
            echo "❌ Container: $CONTAINER_NAME is not running"
            echo ""
            echo "💡 To start: docker-compose up -d celery_worker"
        fi
        ;;
        
    "logs"|"log")
        echo "📋 Worker logs (last 50 lines):"
        echo "================================="
        docker logs --tail=50 -f $CONTAINER_NAME
        ;;
        
    "restart")
        echo "🔄 Restarting worker..."
        docker-compose restart celery_worker
        echo "✅ Worker restarted"
        ;;
        
    "inspect"|"info")
        echo "🔍 Detailed worker inspection:"
        echo "=============================="
        
        if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
            echo "📊 Worker statistics:"
            docker exec $CONTAINER_NAME celery -A services.pdf_tasks inspect stats -d $WORKER_NAME
            
            echo ""
            echo "⚙️  Worker configuration:"
            docker exec $CONTAINER_NAME celery -A services.pdf_tasks inspect conf -d $WORKER_NAME
            
            echo ""
            echo "📝 Registered tasks:"
            docker exec $CONTAINER_NAME celery -A services.pdf_tasks inspect registered -d $WORKER_NAME
        else
            echo "❌ Worker container not running"
        fi
        ;;
        
    "queue"|"q")
        echo "📬 Queue inspection:"
        echo "==================="
        
        # Check Redis queue lengths
        echo "Queue lengths:"
        docker exec astronova_redis redis-cli llen pdf || echo "❌ Cannot connect to Redis"
        
        # Check scheduled tasks
        echo ""
        echo "Scheduled tasks:"
        docker exec $CONTAINER_NAME celery -A services.pdf_tasks inspect scheduled -d $WORKER_NAME 2>/dev/null || echo "ℹ️  No scheduled tasks"
        ;;
        
    "clear")
        echo "🧹 Clearing failed tasks from Redis..."
        docker exec astronova_redis redis-cli flushdb
        echo "✅ Redis queues cleared"
        ;;
        
    "help"|"-h"|"--help")
        echo "AstroNova Celery Worker Monitor"
        echo "==============================="
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  status    - Show worker status and active tasks (default)"
        echo "  logs      - Show worker logs (follow mode)"
        echo "  restart   - Restart the worker container"
        echo "  inspect   - Detailed worker inspection"
        echo "  queue     - Check queue status and scheduled tasks"
        echo "  clear     - Clear failed tasks from Redis"
        echo "  help      - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 status"
        echo "  $0 logs"
        echo "  $0 restart"
        ;;
        
    *)
        echo "❌ Unknown command: $1"
        echo "💡 Use '$0 help' for available commands"
        exit 1
        ;;
esac