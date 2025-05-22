# AkuBox Controller for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

“AkuBox Controller”是一个 Home Assistant 自定义集成，用于通过本地 API 控制和监控 AkuBox 设备。

## 功能

* **系统信息监控：**
    * CPU 使用率
    * 内存使用率 (%)
    * 电池电量
    * 电池状态
    * 设备运行时间
    * 主机名
    * 操作系统信息
    * 系统架构
    * Go 版本
    * Go 协程数
    * 工作目录
* **媒体播放器控制：**
    * 音量调节（设置和步进）

## 安装

### 通过 HACS 安装 (推荐)

1.  确保您已安装 [HACS](https://hacs.xyz/)。
2.  在 HACS 中，导航到 “集成”。
3.  点击右上角的三个点，选择 “自定义存储库”。
4.  在 “存储库” 字段中输入您的 GitHub 仓库 URL (`https://github.com/your_username/your_repository_name`)。
5.  选择 “集成” 作为类别。
6.  点击 “添加”。
7.  在 HACS 中搜索 “AkuBox Controller” 并安装它。
8.  重启 Home Assistant。

### 手动安装

1.  下载最新的 [Release](https://github.com/your_username/your_repository_name/releases)。
2.  将 `custom_components/akubox_controller` 文件夹复制到您的 Home Assistant 配置目录下的 `custom_components` 文件夹中。如果 `custom_components` 文件夹不存在，请创建它。
    目录结构应如下所示：
    ```
    <config_directory>/
    └── custom_components/
        └── akubox_controller/
            ├── __init__.py
            ├── sensor.py
            ├── media_player.py
            ├── manifest.json
            ├── const.py
            ├── api.py
            ├── config_flow.py
            └── translations/
                ├── en.json
                └── zh-Hans.json
    ```
3.  重启 Home Assistant。

## 配置

1.  导航到 Home Assistant 中的 “设置” > “设备与服务”。
2.  点击右下角的 “+ 添加集成” 按钮。
3.  搜索 “AkuBox Controller” 并选择它。
4.  在配置对话框中，输入您的 AkuBox 设备的 IP 地址。
5.  点击 “提交”。

集成将尝试连接到设备并自动添加相关的传感器和媒体播放器实体。

## 选项

配置完成后，您可以通过集成选项调整以下参数：
* 系统信息更新间隔（秒）
* 音量更新间隔（秒）

要访问选项：
1.  导航到 “设置” > “设备与服务”。
2.  找到 AkuBox Controller 集成。
3.  点击 “选项” 或 “配置”。

## 传感器

该集成将创建以下传感器实体 (传感器名称会根据设备的主机名和语言设置本地化)：

* **CPU 使用率:** (`sensor.<device_name>_cpu_usage`)
* **内存使用率:** (`sensor.<device_name>_memory_usage`)
* **电池容量:** (`sensor.<device_name>_battery_capacity`)
* **电池状态:** (`sensor.<device_name>_battery_status`)
* **运行时间:** (`sensor.<device_name>_uptime`)
* **主机名:** (`sensor.<device_name>_hostname`)
* **操作系统:** (`sensor.<device_name>_operating_system`)
* **架构:** (`sensor.<device_name>_architecture`)
* **Go 版本:** (`sensor.<device_name>_go_version`)
* **Go 协程数:** (`sensor.<device_name>_go_routines`)
* **工作目录:** (`sensor.<device_name>_work_directory`)

## 媒体播放器

该集成将创建一个媒体播放器实体，主要用于音量控制：

* **音量控制:** (`media_player.<device_name>_volume_control`)
    * 支持设置音量。
    * 支持增大/减小音量。

## API (供参考)

该集成通过以下 API 端点与 AkuBox 设备通信：

* `GET /api/system/info`: 获取系统信息。
* `GET /api/volume/get`: 获取当前音量。
* `POST /api/volume/set`: 设置音量 (JSON body: `{"volume": 0-100}`)。

## 贡献

欢迎贡献！如果您有任何改进建议或发现任何问题，请随时提交 Pull Request 或在 [Issue Tracker](https://github.com/your_username/your_repository_name/issues) 中报告。

## 免责声明

这是一个非官方的集成。请自行承担使用风险。

## 许可证

[MIT License](LICENSE) (如果您的项目中有 LICENSE 文件，请链接到它)