# 数字人工具

此项目包含可以直接将普通图片和音频转换为会说话的数字人视频的工具。

## 使用方法

### 数字人视频生成器 (`digital_human.py`)

一键式数字人视频生成工具，自动完成人脸裁剪和嘴唇动画创建。

```
python digital_human.py original_image.jpg -a voice.wav -o output_video.mp4
```

参数:
- `original_image.jpg`: 输入的原始人物图像（无需预先裁剪）
- `-a, --audio`: 音频文件路径（WAV、MP3等格式）
- `-o, --output`: 输出视频路径（可选）
- `-d, --duration`: 视频时长，单位为秒（默认：使用音频时长，若无音频则为10秒）
- `--bg_color`: 背景颜色，格式为B G R（默认：50 50 200，偏红色）
- `--fps`: 视频帧率（默认：30）
- `--face_zoom`: 人脸区域缩放因子（默认：1.5，值越大裁剪区域越广）
- `--only_face`: 仅包含面部，不包含肩部（默认：false，包含上身）

### 简单版说话头像生成器 (`simple_talking.py`)

使用两张图片（张嘴和闭嘴状态）快速创建说话视频，更简单易用。

```
python simple_talking.py closed_mouth.jpg open_mouth.jpg -a voice.wav -o output_video.mp4
```

参数:
- `closed_mouth.jpg`: 闭嘴状态的图片
- `open_mouth.jpg`: 张嘴状态的图片
- `-a, --audio`: 音频文件路径（WAV、MP3等格式）
- `-o, --output`: 输出视频路径（可选）
- `-d, --duration`: 视频时长，单位为秒（默认：使用音频时长，若无音频则为10秒）
- `--bg_color`: 背景颜色，格式为B G R（默认：50 50 200）
- `--fps`: 视频帧率（默认：30）

### 高级唇形动画生成器 (`lip_talking.py`)

只改变嘴唇区域的精确动画生成工具，实现平滑过渡的唇形变化。

```
python lip_talking.py base_image.jpg open_mouth_image.jpg -a voice.wav -o output_video.mp4 --smoothness 0.7
```

参数:
- `base_image.jpg`: 基础图片（闭嘴状态）
- `open_mouth_image.jpg`: 张嘴状态的图片（用于提取嘴唇形状）
- `-a, --audio`: 音频文件路径（WAV、MP3等格式）
- `-o, --output`: 输出视频路径（可选）
- `-d, --duration`: 视频时长，单位为秒（默认：使用音频时长，若无音频则为10秒）
- `--bg_color`: 背景颜色，格式为B G R（默认：50 50 200）
- `--fps`: 视频帧率（默认：30）
- `--smoothness`: 嘴唇动画平滑度（0-1之间，越大越平滑，默认：0.5）

### 主要功能

1. **数字人视频生成器**
   - 自动人脸检测与裁剪
   - 音频驱动的嘴唇动画
   - 支持自定义背景与效果

2. **简单版说话头像生成器**
   - 仅需两张图片（张嘴和闭嘴状态）
   - 根据音频振幅自动切换口型
   - 操作简单，效果直观

3. **高级唇形动画生成器**
   - 只改变嘴唇区域，保持面部其他部分不变
   - 使用面部特征点精确定位嘴唇区域
   - 平滑过渡的唇形变化，更自然真实
   - 支持调整平滑度参数

## 安装依赖

```
pip install opencv-python numpy scipy moviepy pydub
pip install dlib  # 用于高级唇形动画生成器
```

您还需要下载面部特征点检测模型（用于高级唇形动画生成器）：
https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2

下载后解压并放置在与脚本相同的目录中。

## 示例用法

### 数字人视频生成器：
```
python digital_human.py person.jpg -a speech.wav
```

### 简单版说话头像生成器：
```
python simple_talking.py person_closed.jpg person_open.jpg -a voice.wav
```

### 高级唇形动画生成器：
```
python lip_talking.py person.jpg person_open.jpg -a voice.wav --smoothness 0.7
```

### 自定义背景颜色和输出路径：
```
python lip_talking.py closed.jpg open.jpg -a voice.wav -o my_video.mp4 --bg_color 200 200 100
```

## 注意事项

- 对于简单版生成器，两张图片应当尺寸一致，否则会自动调整
- 对于高级唇形生成器，两张图片必须是同一人物，且角度、光照条件尽量一致
- 高级唇形生成器需要dlib库和预训练模型
- WAV格式音频通常效果最佳，但也支持其他常见音频格式
- 调整平滑度参数可以改变嘴唇动画的自然程度

### 主要功能

1. **自动人脸检测与裁剪**
   - 使用MediaPipe自动识别人脸位置
   - 智能调整裁剪区域以包含适当的肩部区域

2. **音频驱动的嘴唇动画**
   - 分析音频文件的振幅变化生成同步的嘴唇动作
   - 使用面部关键点精确控制嘴唇动作
   - 即使没有音频文件，也能生成自然的随机嘴唇动画

3. **自定义背景与效果**
   - 可选择纯色背景颜色
   - 调整人脸裁剪范围

## 安装依赖

```
pip install opencv-python mediapipe numpy scipy moviepy
pip install pydub  # 用于音频分析，强烈推荐安装
```

## 示例用法

### 基本用法 - 使用音频生成数字人视频：
```
python digital_human.py person.jpg -a speech.wav
```

### 自定义背景颜色和输出路径：
```
python digital_human.py person.jpg -a voice.wav -o my_video.mp4 --bg_color 200 100 50
```

### 仅使用面部区域的特写镜头：
```
python digital_human.py person.jpg -a voice.wav --only_face --face_zoom 1.8
```

## 注意事项

- 输入图像应当包含清晰的人脸，最好是正面照
- WAV格式音频通常效果最佳，但也支持其他常见音频格式
- 如果检测不到人脸，程序会尝试使用整个原始图像
- 临时文件会在处理完成后自动清理 