# 352 Air Purifier for Home Assistant

这是一个用于 Home Assistant 的 352 空气净化器集成组件。

## 功能特点

-   登录 352 账号自动获取已绑定的设备
-   支持 352 空气净化器的基本控制，包括开关、风速、灯光等。
-   接入净化器的 PM2.5 传感器数据。

## 安装

1. 通过 HACS 安装（推荐）：

    - 在 HACS 中添加此仓库
    - 搜索 "352 Air Purifier" 并安装

2. 手动安装：
    - 下载此仓库
    - 将 `custom_components/hass_352_air_purifier` 目录复制到你的 Home Assistant 配置目录下的 `custom_components` 文件夹中
    - 重启 Home Assistant

## 已测试的设备

-   352 X83

## 许可证

MIT License
