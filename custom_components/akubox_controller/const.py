# /config/custom_components/akubox_controller/const.py
DOMAIN = "akubox_controller"
PLATFORMS = ["sensor", "media_player"] # 我们将创建传感器和媒体播放器实体

CONF_HOST = "host"
DEFAULT_NAME = "AkuBox"

# 更新间隔 (秒)
UPDATE_INTERVAL_SYSTEM = 60  # 系统信息更新频率（例如每分钟）
UPDATE_INTERVAL_VOLUME = 10  # 音量信息更新频率（例如每10秒）

# API Endpoints
API_SYSTEM_INFO = "/api/system/info"
API_VOLUME_GET = "/api/volume/get"
API_VOLUME_SET = "/api/volume/set"

# Sensor types
SENSOR_CPU_USAGE = "cpu_usage"
SENSOR_MEMORY_USAGE_PERCENT = "memory_usage_percent"
SENSOR_BATTERY_CAPACITY = "battery_capacity"
SENSOR_BATTERY_STATUS = "battery_status"
SENSOR_UPTIME = "uptime"
SENSOR_HOSTNAME = "hostname"
SENSOR_OS = "os"
SENSOR_ARCHITECTURE = "architecture"
SENSOR_GO_VERSION = "go_version"
SENSOR_NUM_GOROUTINE = "num_goroutine"
SENSOR_WORK_DIR = "work_dir"

# Attributes for system info
ATTR_CPU_NUM = "num_cpu"
ATTR_GO_MAX_PROC = "go_max_proc"
ATTR_MEMORY_TOTAL_MB = "memory_total_mb"
ATTR_MEMORY_USED_MB = "memory_used_mb"