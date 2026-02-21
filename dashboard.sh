#!/bin/bash
SHARE_DIR="/mnt/sda1/shared"
PID_FILE="$SHARE_DIR/dashboard.pid"
LOG_FILE="$SHARE_DIR/dashboard.log"

start() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "Dashboard is already running (PID $(cat $PID_FILE))"
        return
    fi
    echo "Starting Network Dashboard on port 80..."
    cd "$SHARE_DIR" || exit 1
    nohup sudo python3 dashboard.py > "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    echo "Dashboard started with PID $(cat $PID_FILE)"
    sleep 2  # Give Flask time to start
    tail -n 10 "$LOG_FILE"  # Show the last 10 lines with URLs
}

stop() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping Dashboard (PID $PID)..."
            kill $PID
            rm "$PID_FILE"
            echo "Dashboard stopped."
        else
            rm "$PID_FILE"
            echo "Dashboard not running, PID file removed."
        fi
    else
        echo "No PID file found. Dashboard not running."
    fi
}

update() {
    # Stop dashboard if running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 $PID 2>/dev/null; then
            echo "Stopping Dashboard (PID $PID)..."
            kill $PID
            rm "$PID_FILE"
            echo "Dashboard stopped."
        else
            rm "$PID_FILE"
            echo "Dashboard not running, PID file removed."
        fi
    else
        echo "No PID file found. Dashboard not running."
    fi

    # Start updater in foreground
    echo "Starting updater..."
    sudo python3 /mnt/sda1/shared/Chronos_updater.py
    echo "Updater finished."
}


reboot() {
    stop
    start
}

case "$1" in
start) start ;;
stop) stop ;;
reboot) reboot ;;
update) update ;;
*) echo "Usage: $0 {start|stop|reboot}" ;;
esac
