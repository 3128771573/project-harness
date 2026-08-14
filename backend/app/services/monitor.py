"""系统监控服务：读取宿主 CPU/内存/磁盘/uptime 指标"""
import os
from datetime import datetime, timedelta, timezone


def _read_cpu_percent() -> int:
    """读取 /proc/stat 计算 1s 间隔 CPU 使用率"""
    try:
        with open("/proc/stat") as f:
            line = f.readline().split()
        idle = int(line[4]) + int(line[5])  # idle + iowait
        total = sum(int(v) for v in line[1:])
        prev = (idle, total)
        # 第二次采样
        import time

        time.sleep(0.5)
        with open("/proc/stat") as f:
            line = f.readline().split()
        idle2 = int(line[4]) + int(line[5])
        total2 = sum(int(v) for v in line[1:])
        d_idle = idle2 - prev[0]
        d_total = total2 - prev[1]
        if d_total <= 0:
            return 0
        return max(0, min(100, round(100 * (1 - d_idle / d_total))))
    except Exception:
        return 0


def _read_memory_percent() -> int:
    """内存使用率"""
    try:
        with open("/proc/meminfo") as f:
            meminfo = {}
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                meminfo[key] = int(parts[1])
        total = meminfo.get("MemTotal", 1)
        available = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
        used = total - available
        return max(0, min(100, round(100 * used / total)))
    except Exception:
        return 0


def _read_disk_percent() -> int:
    """根分区磁盘使用率"""
    try:
        statvfs = os.statvfs("/")
        total = statvfs.f_blocks * statvfs.f_frsize
        free = statvfs.f_bavail * statvfs.f_frsize
        used = total - free
        return max(0, min(100, round(100 * used / total)))
    except Exception:
        return 0


def _read_uptime() -> str:
    """运行时长，格式 '20 days, 3:15'"""
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        if days > 0:
            return f"{days} days, {hours}:{minutes:02d}"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
    except Exception:
        return "unknown"


def get_system_status() -> dict:
    """汇总系统指标，供 /admin/system/status 使用"""
    return {
        "cpu": _read_cpu_percent(),
        "memory": _read_memory_percent(),
        "disk": _read_disk_percent(),
        "uptime": _read_uptime(),
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
