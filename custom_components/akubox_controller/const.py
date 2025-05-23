# /config/custom_components/akubox_controller/const.py
DOMAIN = "akubox_controller"
PLATFORMS = ["sensor", "media_player", "switch"]

CONF_HOST = "host"
CONF_CUSTOM_NAME = "custom_name" # 新增：用于自定义名称的常量
DEFAULT_NAME = "AkuBox"
GENERIC_HOSTNAMES = ["akubox", "localhost", "unknown", "default", "system"] # 可根据需要添加更多通用主机名

# 更新间隔 (秒)
UPDATE_INTERVAL_SYSTEM = 60
UPDATE_INTERVAL_VOLUME = 10
UPDATE_INTERVAL_SWITCH = 300 # 开关状态默认轮询间隔 (如果使用协调器或单独轮询)

# API Endpoints
API_SYSTEM_INFO = "/api/system/info"
API_VOLUME_GET = "/api/volume/get"
API_VOLUME_SET = "/api/volume/set"

# 开关 API 端点 (使用不同端口)
API_DLNA_STATE = "/dlna/state" # 用于 GET 和 POST
API_LED_LOGO_STATE = "/device/led_logo_state" # 用于 GET 和 POST

# Sensor types
SENSOR_CPU_USAGE = "cpu_usage"
SENSOR_MEMORY_USAGE_PERCENT = "memory_usage_percent"
SENSOR_BATTERY_LEVEL = "battery_level"
SENSOR_BATTERY_STATUS = "battery_status"
SENSOR_UPTIME = "uptime"
SENSOR_HOSTNAME = "hostname"
SENSOR_OS = "os"
SENSOR_ARCHITECTURE = "architecture"
SENSOR_GO_VERSION = "go_version"
SENSOR_NUM_GOROUTINE = "num_goroutine"
SENSOR_WORK_DIR = "work_dir"

# Switch types
SWITCH_DLNA = "dlna_state_switch"
SWITCH_LED_LOGO = "led_logo_state_switch"

# Attributes for system info
ATTR_CPU_NUM = "num_cpu"
ATTR_GO_MAX_PROC = "go_max_proc"
ATTR_MEMORY_TOTAL_MB = "memory_total_mb"
ATTR_MEMORY_USED_MB = "memory_used_mb"

# API port for switches
API_PORT_SWITCHES = 2268