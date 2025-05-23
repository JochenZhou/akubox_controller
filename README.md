# AkuBox Controller for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

**提示:代码完全由AI生成，我也看不懂代码，必定存在未知风险，请自行承担使用此集成的风险。**

“AkuBox Controller”是一个 Home Assistant 自定义集成，用于通过本地 API 控制和监控 AkuBox 设备。它允许用户查看设备状态、控制媒体播放音量以及操作特定开关。

## 功能

* **系统信息监控：**
    * CPU 使用率 (%)
    * 内存使用率 (%)
    * 电池电量 (%)
    * 电池状态
    * 设备运行时间 (以时间戳形式)
    * 主机名
    * 操作系统信息
    * 系统架构
    * Go 语言版本
    * 当前 Go 协程数
    * 设备工作目录
* **媒体播放器控制：**
    * 音量调节（范围 0-63）
    * 支持音量增大/减小步进
* **开关控制 (通过 IP:2268 端口)：**
    * DLNA 服务开关 (GET 获取状态，POST 切换状态，请求/响应体为纯文本 "on"或"off")
    * LED Logo 灯开关 (GET 获取状态，POST 切换状态，请求/响应体为纯文本 "on"或"off")

## 安装

### 通过 HACS 安装 (推荐)

1.  确保您已安装 [HACS](https://hacs.xyz/)。
2.  在 HACS 中，导航到 “集成”。
3.  点击右上角的三个点，选择 “自定义存储库”。
4.  在 “存储库” 字段中输入 `https://github.com/JochenZhou/akubox_controller`。
5.  选择 “集成” 作为类别。
6.  点击 “添加”。
7.  在 HACS 中搜索 “AkuBox Controller” 并安装它。
8.  重启 Home Assistant。

### 手动安装

1.  访问 `https://github.com/JochenZhou/akubox_controller` 并下载最新的 [Release](https://github.com/JochenZhou/akubox_controller/releases)。
2.  将 `custom_components/akubox_controller` 文件夹完整复制到您的 Home Assistant 配置目录下的 `custom_components` 文件夹中。如果 `custom_components` 文件夹不存在，请创建它。
    最终目录结构应如下所示：
    ```
    <config_directory>/
    └── custom_components/
        └── akubox_controller/
            ├── __init__.py
            ├── api.py
            ├── config_flow.py
            ├── const.py
            ├── manifest.json
            ├── media_player.py
            ├── sensor.py
            ├── switch.py
            └── translations/
                ├── en.json
                └── zh-Hans.json
    ```
3.  重启 Home Assistant。

## 配置

1.  导航到 Home Assistant 中的 “设置” > “设备与服务”。
2.  点击右下角的 “+ 添加集成” 按钮。
3.  搜索 “AkuBox Controller” 并选择它。
4.  在配置对话框中：
    * 输入您的 AkuBox 设备的 **IP 地址**。
    * （可选）输入一个**自定义名称**，以便在有多台设备时轻松区分（例如“客厅 AkuBox”）。 如果留空，系统会尝试使用设备的主机名或IP地址生成一个默认名称。
5.  点击 “提交”。

集成将尝试连接到设备并自动添加相关的传感器、媒体播放器和开关实体。

## 选项

在集成添加成功后，您可以通过集成的“选项”功能调整以下参数：

* **系统信息更新间隔 (秒)**：设置获取 CPU、内存等系统信息的频率。
* **音量更新间隔 (秒)**：设置获取设备音量状态的频率。

要访问选项：
1.  导航到 “设置” > “设备与服务”。
2.  找到已添加的 AkuBox Controller 集成实例。
3.  点击对应实例卡片上的“选项”或“配置”（取决于HA版本和主题，通常是三个点菜单内）。

## 实体

该集成将为每个配置的 AkuBox 设备创建以下实体。实体名称会基于您在配置时提供的自定义名称或系统生成的设备名称，并附加一个描述性后缀（例如“AkuBox (客厅) CPU 使用率”）。

### 传感器 (Sensor)
* CPU 使用率 (`sensor.<device_name>_cpu_usage`)
* 内存使用率 (`sensor.<device_name>_memory_usage_percent`)
* 电池电量 (`sensor.<device_name>_battery_level`)
* 电池状态 (`sensor.<device_name>_battery_status`)
* 运行时间 (`sensor.<device_name>_uptime`)
* 主机名 (`sensor.<device_name>_hostname`)
* 操作系统 (`sensor.<device_name>_os`)
* 架构 (`sensor.<device_name>_architecture`)
* Go 版本 (`sensor.<device_name>_go_version`)
* Go 协程数 (`sensor.<device_name>_num_goroutine`)
* 工作目录 (`sensor.<device_name>_work_dir`)

### 媒体播放器 (Media Player)
* 音量控制 (`media_player.<device_name>_volume_control`)
    * 支持将音量设置为 0 到 63 之间的值。
    * 支持通过服务调用或UI按钮增大/减小音量。

### 开关 (Switch)
* DLNA 服务 (`switch.<device_name>_dlna_service`)
* LED Logo 灯 (`switch.<device_name>_led_logo_light`)

## API 端点 (供开发者参考)

该集成通过以下本地 API 端点与 AkuBox 设备进行通信：

* **主 API (默认端口 80):**
    * `GET /api/system/info`: 获取系统详细信息。
    * `GET /api/volume/get`: 获取当前音量值。
    * `POST /api/volume/set`: 设置音量。请求体为 JSON，例如: `{"volume": 30}` (音量范围 0-63)。
* **开关控制 API (端口 2268):**
    * `GET /dlna/state`: 获取 DLNA 服务状态。响应体为纯文本: `"on"` 或 `"off"`。
    * `POST /dlna/state`: 设置 DLNA 服务状态。请求体为纯文本: `"on"` 或 `"off"` (Content-Type: text/plain)。
    * `GET /device/led_logo_state`: 获取 LED Logo 灯状态。响应体为纯文本: `"on"` 或 `"off"`。
    * `POST /device/led_logo_state`: 设置 LED Logo 灯状态。请求体为纯文本: `"on"` 或 `"off"` (Content-Type: text/plain)。

## 贡献

欢迎各种形式的贡献！如果您有任何改进建议、发现 Bug 或希望添加新功能，请随时在 `https://github.com/JochenZhou/akubox_controller/issues` 提交 Issue 或创建 Pull Request。

## 免责声明

这是一个由社区成员开发的非官方集成，与 AkuBox 设备的制造商无关。请自行承担使用此集成的风险。

## 许可证

本项目采用 [MIT License](https://github.com/JochenZhou/akubox_controller/blob/main/LICENSE) 授权。(请确保您的仓库中包含一个 LICENSE 文件，并且此链接指向正确的位置，例如主分支下的 LICENSE 文件。)

---
## 致谢

本项目在开发过程中得到了以下开发者和项目的帮助与启发，在此表示衷心感谢：

* **zheng1**
* **冰奇**
* **AkuRobot 项目** ([https://github.com/jimieguang/AkuRobot](https://github.com/jimieguang/AkuRobot))

此外，本项目的部分代码和文档是在 Google AI 助手的协助下生成的。
