# SuperGesture

基于 MediaPipe 的手势虚拟触控板，通过摄像头识别手势控制鼠标。

## 手势操作

| 手势 | 功能 |
|------|------|
| 右手张开 + 移动 | 移动光标 |
| 右手握拳 + 移动 | 拖拽 |
| 右手 OK / 捏合 | 点击（快速触发双击） |
| 左手握拳 + 上下移动 | 滚轮滚动 |

绿色区域为追踪区，红色边框为边缘自动移动区。鼠标甩到左上角可紧急停止。

## 安装

```bash
pip install -r requirements.txt
```

下载 MediaPipe 手部检测模型并放到项目根目录：

```bash
curl -L -o hand_landmarker.task \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
```

## 运行

```bash
python main.py
```

按 `q` 退出。
