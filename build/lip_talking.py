import cv2
import numpy as np
import argparse
import os
import time as time_module
from moviepy.editor import VideoFileClip, AudioFileClip
import dlib
import math
import tempfile
import subprocess
import shutil

class LipTalkingGenerator:
    def __init__(self, base_image, open_mouth_image, audio_path=None, output_path=None, 
                 duration=10, bg_color=(50, 50, 200), fps=30, smoothness=0.5):
        """
        使用基础图片和张嘴图片创建唇形动画，只改变嘴部区域
        
        参数:
            base_image: 基础图片路径（闭嘴状态）
            open_mouth_image: 张嘴图片路径（用于提取嘴唇形状）
            audio_path: 音频文件路径（可选）
            output_path: 输出视频路径
            duration: 视频时长（秒）
            bg_color: 背景颜色 (B,G,R)
            fps: 帧率
            smoothness: 嘴唇动画平滑度 (0-1)，越大越平滑
        """
        self.base_image_path = base_image
        self.open_mouth_image_path = open_mouth_image
        self.audio_path = audio_path
        
        # 设置默认输出路径
        if output_path is None:
            base_name, _ = os.path.splitext(base_image)
            self.output_path = f"{base_name}_lip_talking.mp4"
        else:
            self.output_path = output_path
            
        self.duration = duration
        self.bg_color = bg_color
        self.fps = fps
        self.smoothness = max(0.1, min(0.9, smoothness))  # 限制在0.1-0.9之间
        
        # 存储检测到的嘴唇区域
        self.mouth_region = None
        self.detector = None
        self.predictor = None
        self.frames = []
        self.verbose = False  # 控制输出详细程度
        
    def load_images(self):
        """加载基础图片和张嘴图片，检测面部关键点"""
        if self.verbose:
            print(f"加载图片: {self.base_image_path} 和 {self.open_mouth_image_path}")
        else:
            print("加载图片...")
        
        # 读取图像
        self.base_image = cv2.imread(self.base_image_path)
        self.open_image = cv2.imread(self.open_mouth_image_path)
        
        if self.base_image is None:
            raise ValueError(f"无法加载基础图片: {self.base_image_path}")
        if self.open_image is None:
            raise ValueError(f"无法加载张嘴图片: {self.open_mouth_image_path}")
            
        # 确保两张图片尺寸一致
        if self.base_image.shape != self.open_image.shape:
            print(f"警告: 两张图片尺寸不一致。将调整张嘴图片尺寸以匹配基础图片。")
            self.open_image = cv2.resize(self.open_image, 
                                        (self.base_image.shape[1], self.base_image.shape[0]))
        
        try:
            # 保存图片的备份，以便在检测失败时使用简单模式
            self.has_face_landmarks = False
            
            # 加载人脸检测器和关键点预测器
            print("尝试加载dlib面部检测器...")
            try:
                self.detector = dlib.get_frontal_face_detector()
                print("面部检测器加载成功")
            except Exception as e:
                print(f"加载面部检测器失败: {str(e)}")
                self.detector = None
            
            # 尝试加载预训练模型，如果找不到则提示下载
            model_path = "shape_predictor_68_face_landmarks.dat"
            if not os.path.exists(model_path):
                print(f"错误: 找不到面部特征点检测模型: {model_path}")
                print("请从以下地址下载: https://github.com/davisking/dlib-models/raw/master/shape_predictor_68_face_landmarks.dat.bz2")
                print("下载后解压并放置在当前目录")
                self.detect_mouth_simple()
                return
            
            try:
                print(f"尝试加载面部特征点模型: {model_path}")
                self.predictor = dlib.shape_predictor(model_path)
                print("面部特征点模型加载成功")
            except Exception as e:
                print(f"加载面部特征点模型失败: {str(e)}")
                self.predictor = None
                self.detect_mouth_simple()
                return
            
            # 检测基础图片中的嘴唇区域
            success = self.detect_mouth_region()
            if not success:
                print("面部关键点检测失败，使用简单模式")
                self.detect_mouth_simple()
            else:
                self.has_face_landmarks = True
                # 预处理嘴唇区域，调整张嘴图片的颜色以匹配闭嘴图片
                self.preprocess_mouth_region()
            
        except ImportError as e:
            print(f"警告: dlib导入失败 ({e})。将使用简单的图片切换方式。")
            self.detector = None
            self.predictor = None
            self.detect_mouth_simple()

    def detect_mouth_simple(self):
        """当面部检测失败时，使用简单的区域检测方法"""
        print("使用简单模式检测嘴部区域...")
        
        # 将整个图像的中下部分视为嘴部区域
        h, w = self.base_image.shape[:2]
        
        # 确定可能的嘴部区域（图像的中下部）
        min_x = int(w * 0.25)  # 左侧25%的位置
        min_y = int(h * 0.5)   # 上侧50%的位置
        max_x = int(w * 0.75)  # 右侧75%的位置
        max_y = int(h * 0.9)   # 下侧90%的位置
        
        self.mouth_region = (min_x, min_y, max_x, max_y)
        print(f"简单模式检测到嘴部区域: {self.mouth_region}")
        
        # 创建基础的圆形遮罩
        mask = np.zeros((max_y - min_y, max_x - min_x), dtype=np.uint8)
        center_x = (max_x - min_x) // 2
        center_y = (max_y - min_y) // 2
        radius = min(center_x, center_y) * 0.8
        
        # 创建圆形嘴部区域遮罩
        cv2.circle(mask, (center_x, center_y), int(radius), 255, -1)
        
        # 平滑边缘
        self.simple_mouth_mask = cv2.GaussianBlur(mask, (21, 21), 0)
        
        # 简单的颜色匹配，匹配整个区域的平均颜色
        self.match_colors_simple()
    
    def match_colors_simple(self):
        """简单模式下的颜色匹配"""
        if not hasattr(self, 'mouth_region'):
            return
            
        min_x, min_y, max_x, max_y = self.mouth_region
        
        # 简单颜色匹配
        base_area = self.base_image[min_y:max_y, min_x:max_x]
        open_area = self.open_image[min_y:max_y, min_x:max_x]
        
        # 匹配平均颜色
        for c in range(3):  # BGR通道
            base_mean = np.mean(base_area[:, :, c])
            open_mean = np.mean(open_area[:, :, c])
            
            # 安全检查
            if open_mean <= 0:
                continue
                
            factor = base_mean / open_mean
            factor = min(1.5, max(0.5, factor))  # 限制调整范围
            
            # 应用颜色校正
            adjusted = open_area[:, :, c].astype(np.float32) * factor
            adjusted = np.clip(adjusted, 0, 255).astype(np.uint8)
            self.open_image[min_y:max_y, min_x:max_x, c] = adjusted
        
        print("简单模式颜色匹配完成")

    def detect_mouth_region(self):
        """检测嘴唇区域"""
        if self.detector is None or self.predictor is None:
            print("未加载面部检测器，跳过嘴唇区域检测")
            return False
            
        # 转换为灰度图像
        gray = cv2.cvtColor(self.base_image, cv2.COLOR_BGR2GRAY)
        
        # 检测人脸
        faces = self.detector(gray)
        if len(faces) == 0:
            print("警告: 未检测到人脸，将使用简单图片切换")
            return False
            
        # 获取第一个检测到的人脸
        face = faces[0]
        
        # 获取面部关键点
        landmarks = self.predictor(gray, face)
        
        # 获取完整的面部关键点
        face_points = []
        for i in range(68):  # 总共68个关键点
            x = landmarks.part(i).x
            y = landmarks.part(i).y
            face_points.append((x, y))
        
        # 提取嘴唇和下巴区域关键点
        # 嘴唇: 48-67
        # 下巴: 0-16
        mouth_chin_points = []
        for i in range(48, 68):  # 嘴唇
            mouth_chin_points.append(face_points[i])
        for i in range(5, 13):  # 下巴中间部分
            mouth_chin_points.append(face_points[i])
        
        # 计算扩展的嘴唇和下巴区域边界框
        min_x = min(p[0] for p in mouth_chin_points)
        min_y = min(p[1] for p in mouth_chin_points)
        max_x = max(p[0] for p in mouth_chin_points)
        max_y = max(p[1] for p in mouth_chin_points)
        
        # 扩大区域以包含更多周围区域
        # 减小横向扩展，增加纵向扩展到下巴
        h_padding = int((max_x - min_x) * 0.2)  # 水平方向扩展
        v_padding_top = int((max_y - min_y) * 0.2)  # 上方扩展
        v_padding_bottom = int((max_y - min_y) * 0.6)  # 下方扩展更多，包含下巴
        
        min_x = max(0, min_x - h_padding)
        min_y = max(0, min_y - v_padding_top)
        max_x = min(self.base_image.shape[1], max_x + h_padding)
        max_y = min(self.base_image.shape[0], max_y + v_padding_bottom)
        
        # 存储嘴唇和下巴区域
        self.mouth_region = (min_x, min_y, max_x, max_y)
        self.mouth_landmarks = mouth_chin_points
        
        print(f"检测到嘴唇和下巴区域: {self.mouth_region}")

        # 预处理嘴唇区域，调整张嘴图片的颜色以匹配闭嘴图片
        self.preprocess_mouth_region()
        return True
    
    def preprocess_mouth_region(self):
        """预处理嘴唇区域，调整颜色匹配"""
        if not self.mouth_region:
            return
            
        min_x, min_y, max_x, max_y = self.mouth_region
        
        # 提取嘴唇区域
        base_mouth = self.base_image[min_y:max_y, min_x:max_x].copy()
        open_mouth = self.open_image[min_y:max_y, min_x:max_x].copy()
        
        # 计算两个图像的差异来找出主要变化区域（嘴唇部分）
        base_lab = cv2.cvtColor(base_mouth, cv2.COLOR_BGR2LAB)
        open_lab = cv2.cvtColor(open_mouth, cv2.COLOR_BGR2LAB)
        
        # 转为LAB色彩空间更精确地调整颜色
        for c in range(3):  # L, A, B 通道
            # 获取每个通道
            base_channel = base_lab[:, :, c].astype(np.float32)
            open_channel = open_lab[:, :, c].astype(np.float32)
            
            # 计算差异和掩码，只在主要区域外调整颜色
            diff = cv2.absdiff(base_lab[:,:,0], open_lab[:,:,0])
            _, change_mask = cv2.threshold(diff, 15, 255, cv2.THRESH_BINARY)
            inverse_mask = cv2.bitwise_not(change_mask)
            
            # 计算非变化区域的平均值差异
            mask_pixels = np.sum(inverse_mask > 0)
            if mask_pixels > 0:
                base_mean = np.sum(base_channel * (inverse_mask > 0)) / mask_pixels
                open_mean = np.sum(open_channel * (inverse_mask > 0)) / mask_pixels
                
                # 计算调整因子
                if open_mean != 0:
                    factor = base_mean / open_mean
                    # 限制调整范围，防止过度校正
                    factor = min(1.2, max(0.8, factor))
                    
                    # 应用平滑的颜色调整
                    adjusted_channel = open_channel * factor
                    # 确保值在正确范围内
                    if c == 0:  # L通道范围0-255
                        adjusted_channel = np.clip(adjusted_channel, 0, 255)
                    else:  # a,b通道范围-127到127
                        adjusted_channel = np.clip(adjusted_channel, -127, 127)
                    
                    # 将调整后的通道应用回原图像
                    open_lab[:, :, c] = adjusted_channel.astype(np.uint8)
        
        # 转回BGR色彩空间
        adjusted_open_mouth = cv2.cvtColor(open_lab, cv2.COLOR_LAB2BGR)
        
        # 仅在非嘴唇区域应用颜色校正，保留嘴唇区域的原始外观
        kernel = np.ones((5, 5), np.uint8)
        change_mask = cv2.dilate(change_mask, kernel, iterations=1)
        
        # 创建渐变边缘，使颜色过渡更加平滑
        change_mask = cv2.GaussianBlur(change_mask, (9, 9), 0)
        change_mask = change_mask.astype(np.float32) / 255.0
        
        # 组合原始张嘴图像和颜色调整后的图像
        blended = np.zeros_like(open_mouth)
        
        for c in range(3):
            orig_channel = self.open_image[min_y:max_y, min_x:max_x, c].astype(np.float32)
            adj_channel = adjusted_open_mouth[:, :, c].astype(np.float32)
            blended[:, :, c] = change_mask * orig_channel + (1 - change_mask) * adj_channel
            
        # 更新开口图像区域
        self.open_image[min_y:max_y, min_x:max_x] = blended.astype(np.uint8)
        
        # 进行第二次颜色校正，防止泛蓝光问题
        # 获取嘴唇区域
        mouth_diff = cv2.absdiff(self.base_image[min_y:max_y, min_x:max_x], self.open_image[min_y:max_y, min_x:max_x])
        mouth_mask = cv2.threshold(cv2.cvtColor(mouth_diff, cv2.COLOR_BGR2GRAY), 15, 255, cv2.THRESH_BINARY)[1]
        
        # 检查嘴唇区域的蓝色通道是否过度
        b_diff = self.open_image[min_y:max_y, min_x:max_x, 0].astype(np.float32) - self.base_image[min_y:max_y, min_x:max_x, 0].astype(np.float32)
        b_diff_mean = np.mean(b_diff)
        
        # 如果蓝色通道差异过大，进行校正
        if b_diff_mean > 5:  # 蓝色偏高
            correction = np.ones_like(self.open_image[min_y:max_y, min_x:max_x])
            correction[:,:,0] = 0.85  # 降低蓝色通道
            # 手动执行颜色校正，避免cv2.multiply的类型问题
            open_region = self.open_image[min_y:max_y, min_x:max_x].astype(np.float32)
            corrected = np.zeros_like(open_region)
            for c in range(3):
                corrected[:,:,c] = open_region[:,:,c] * correction[:,:,c]
            corrected = corrected.astype(np.uint8)
            
            mask_3d = np.stack([mouth_mask, mouth_mask, mouth_mask], axis=2) / 255.0
            self.open_image[min_y:max_y, min_x:max_x] = (mask_3d * corrected + (1-mask_3d) * self.open_image[min_y:max_y, min_x:max_x]).astype(np.uint8)
        
        print("已调整张嘴图片的颜色以匹配基础图片")

    def generate_talking_animation(self):
        """生成说话动画序列"""
        # 如果有音频文件，使用音频振幅驱动嘴部动作
        if self.audio_path and os.path.exists(self.audio_path):
            self.create_audio_driven_animation()
        else:
            # 否则创建简单的随机动画
            self.create_random_animation()
    
    def create_audio_driven_animation(self):
        """使用音频驱动嘴巴开合"""
        try:
            from pydub import AudioSegment
            import numpy as np
            
            if self.verbose:
                print(f"加载音频: {self.audio_path}")
            else:
                print("加载音频...")
            
            # 检查是否提供了音频文件
            if not self.audio_path or not os.path.exists(self.audio_path):
                print("没有提供音频文件或文件不存在，将创建随机动画")
                self.create_random_animation()
                return
                
            try:
                # 加载音频并获取振幅数据
                audio = AudioSegment.from_file(self.audio_path)
                audio_array = np.array(audio.get_array_of_samples())
                if self.verbose:
                    print(f"音频加载成功: 长度={len(audio_array)}, 采样率={audio.frame_rate}")
            except Exception as e:
                print(f"音频加载失败: {str(e)}")
                self.create_random_animation()
                return
            
            # 规范化音频数据
            if np.max(np.abs(audio_array)) > 0:
                normalized_audio = np.abs(audio_array) / np.max(np.abs(audio_array))
            else:
                print("警告: 音频信号全为零，无法归一化。使用随机动画代替。")
                self.create_random_animation()
                return
            
            # 计算音频时长（秒）
            audio_duration = len(audio_array) / audio.frame_rate
            if self.verbose:
                print(f"音频时长: {audio_duration:.2f} 秒")
            
            # 如果未指定视频时长，使用音频时长
            if self.duration is None or self.duration <= 0:
                self.duration = audio_duration
                if self.verbose:
                    print(f"使用音频时长作为视频时长: {self.duration:.2f} 秒")
            
            # 创建时间点和对应的口型状态
            total_frames = int(self.duration * self.fps)
            print(f"生成 {total_frames} 帧的视频...")
            
            # 使用语音分析窗口，使用更短的分析窗口捕捉快速变化的语音
            window_duration = 0.025  # 25毫秒窗口，标准语音处理窗口大小
            samples_per_window = int(window_duration * audio.frame_rate)
            
            # 计算每帧对应的音频窗口
            frame_windows = []
            for i in range(total_frames):
                # 计算当前帧对应的音频时间点
                t = i / self.fps
                # 确定音频窗口索引
                center_sample = int(t * audio.frame_rate)
                start_sample = max(0, center_sample - samples_per_window // 2)
                end_sample = min(len(normalized_audio), center_sample + samples_per_window // 2)
                frame_windows.append((start_sample, end_sample))
            
            # 计算音频特征
            all_amplitudes = []
            for start, end in frame_windows:
                if end > start:
                    # 计算窗口内的平均振幅
                    amplitude = np.mean(normalized_audio[start:end])
                    # 应用非线性缩放，突出较低音量的变化
                    amplitude = amplitude ** 0.6  # 平方根变换，增强低振幅识别度
                    all_amplitudes.append(amplitude)
                else:
                    all_amplitudes.append(0)
            
            # 提高振幅对比度，使动画更明显
            mean_amp = np.mean(all_amplitudes)
            max_amp = np.max(all_amplitudes)
            
            # 应用自适应阈值，根据实际音频振幅调整
            if max_amp < 0.3:  # 音频振幅很小
                boost_factor = 3.0  # 大幅增强
            elif max_amp < 0.6:  # 中等振幅
                boost_factor = 2.0  # 中等增强
            else:  # 振幅充足
                boost_factor = 1.5  # 轻微增强
            
            # 归一化并增强振幅
            enhanced_amplitudes = []
            for amp in all_amplitudes:
                # 减去平均值，然后乘以放大因子，再加回平均值
                enhanced = (amp - mean_amp) * boost_factor + mean_amp
                # 应用曲线变换，使低振幅更加明显
                if enhanced < mean_amp:
                    enhanced = enhanced * 0.7  # 降低低振幅的值，使闭嘴状态更明显
                enhanced = max(0, min(1.0, enhanced))  # 限制在[0,1]范围内
                enhanced_amplitudes.append(enhanced)
            
            all_amplitudes = enhanced_amplitudes
            
            if self.verbose:
                print(f"音频振幅统计: 平均={mean_amp:.4f}, 最大={max_amp:.4f}")
            
            # 应用更加智能的平滑处理
            # 使用自适应窗口大小，音量变化大的地方使用小窗口，变化小的使用大窗口
            smoothed_amplitudes = np.zeros_like(all_amplitudes)
            
            # 先计算振幅变化率
            amp_diff = np.abs(np.diff(np.array(all_amplitudes), prepend=all_amplitudes[0]))
            
            # 根据变化率确定窗口大小
            smooth_max = max(1, int(self.fps * self.smoothness))  # 最大平滑窗口
            smooth_min = max(1, int(smooth_max * 0.3))  # 最小平滑窗口
            
            for i in range(len(all_amplitudes)):
                # 变化率大的地方窗口小，变化小的地方窗口大
                change_rate = amp_diff[i] / max(0.001, max_amp)
                adaptive_window = max(smooth_min, int(smooth_max * (1 - min(0.8, change_rate * 10))))
                
                # 应用可变窗口平滑
                start_idx = max(0, i - adaptive_window // 2)
                end_idx = min(len(all_amplitudes), i + adaptive_window // 2)
                smoothed_amplitudes[i] = np.mean(all_amplitudes[start_idx:end_idx])
            
            # 平滑后调整嘴唇开合频率，避免开合过于频繁
            # 设置最小嘴唇状态持续时间
            min_state_duration = max(1, int(self.fps * 0.08))  # 至少80ms
            
            # 应用状态持续时间约束
            open_state = False
            last_state_change = 0
            threshold = 0.08  # 状态变化阈值调整
            
            for i in range(1, len(smoothed_amplitudes)):
                # 检查是否满足状态变化的时间要求
                state_duration = i - last_state_change
                if state_duration < min_state_duration:
                    # 如果状态持续时间不够，维持当前状态
                    if open_state:
                        smoothed_amplitudes[i] = max(smoothed_amplitudes[i], smoothed_amplitudes[i-1] * 0.95)
                    else:
                        smoothed_amplitudes[i] = min(smoothed_amplitudes[i], smoothed_amplitudes[i-1] * 1.05)
                else:
                    # 判断状态是否需要变化
                    if (open_state and smoothed_amplitudes[i] < threshold * 0.7) or \
                       (not open_state and smoothed_amplitudes[i] > threshold * 1.3):
                        # 状态变化
                        open_state = not open_state
                        last_state_change = i
            
            # 降低阈值来确定嘴巴开合，使动画更明显
            threshold = 0.06  # 降低基础阈值，确保有足够的嘴部动作
            if self.verbose:
                print(f"使用开口阈值: {threshold:.2f}")
            
            # 预先计算唇形区域掩码
            if hasattr(self, 'mouth_region') and self.mouth_region:
                min_x, min_y, max_x, max_y = self.mouth_region
                if self.verbose:
                    print(f"使用检测到的嘴部区域: ({min_x}, {min_y}, {max_x}, {max_y})")
                
                # 获取嘴唇区域
                base_mouth = self.base_image[min_y:max_y, min_x:max_x]
                open_mouth = self.open_image[min_y:max_y, min_x:max_x]
                
                # 如果在简单模式下，使用已经计算好的掩码
                if hasattr(self, 'simple_mouth_mask') and not self.has_face_landmarks:
                    if self.verbose:
                        print("使用简单模式遮罩")
                    mouth_mask = self.simple_mouth_mask
                else:
                    # 计算RGB差异掩码
                    if self.verbose:
                        print("计算嘴部区域差异遮罩")
                    diff_mask = np.zeros_like(base_mouth[:,:,0])
                    
                    # 累加三个通道的差异，提高精度
                    for c in range(3):
                        # 计算每个通道的差异
                        channel_diff = cv2.absdiff(base_mouth[:,:,c], open_mouth[:,:,c])
                        diff_mask = cv2.add(diff_mask, channel_diff)
                    
                    # 提取嘴唇变化区域
                    _, lip_mask = cv2.threshold(diff_mask, 25, 255, cv2.THRESH_BINARY)
                    
                    # 使用中等大小的核进行膨胀，扩展嘴唇区域
                    kernel = np.ones((3, 3), np.uint8)
                    lip_mask = cv2.dilate(lip_mask, kernel, iterations=2)  # 增加膨胀次数
                    
                    # 生成动态掩码，适应不同的嘴部变化
                    h, w = lip_mask.shape
                    dynamic_mask = np.zeros_like(lip_mask, dtype=np.float32)
                    
                    # 计算嘴唇区域中心
                    lip_pixels = np.where(lip_mask > 0)
                    if len(lip_pixels[0]) > 0:
                        # 计算嘴唇区域中心
                        center_y = int(np.mean(lip_pixels[0]))
                        center_x = int(np.mean(lip_pixels[1]))
                        # 将中心点稍微下移，更接近下巴
                        center_y = min(h-1, int(center_y * 1.1))
                        
                        # 创建从中心点向外的径向渐变
                        for y in range(h):
                            for x in range(w):
                                # 计算到中心的距离
                                distance = np.sqrt((y - center_y)**2 + (x - center_x)**2)
                                # 最大半径为区域高度的一半
                                max_radius = h * 0.7
                                if distance < max_radius:
                                    # 根据距离创建平滑衰减
                                    weight = 1.0 - (distance / max_radius)**2
                                    # 强调下巴区域的权重
                                    if y > center_y:
                                        # 下巴区域权重衰减较慢
                                        weight = min(1.0, weight * 1.5)
                                    dynamic_mask[y, x] = weight * 255
                    else:
                        if self.verbose:
                            print("警告: 未检测到明显的嘴唇区域差异，使用简单圆形掩码")
                        # 创建简单的圆形掩码
                        center_x, center_y = w // 2, h // 2
                        radius = min(w, h) // 3
                        cv2.circle(dynamic_mask, (center_x, center_y), radius, 255, -1)
                                
                    # 组合动态掩码和嘴唇掩码，增加掩码权重
                    combined_mask = np.maximum(lip_mask.astype(np.float32), dynamic_mask * 0.8)
                    final_mask = np.clip(combined_mask, 0, 255).astype(np.uint8)
                    
                    # 应用高斯模糊使边缘更平滑
                    mouth_mask = cv2.GaussianBlur(final_mask, (9, 9), 0)
                    
                    # 确保掩码有足够的值
                    if np.max(mouth_mask) < 50:  # 如果最大值太小
                        if self.verbose:
                            print("警告: 掩码值太低，增强掩码对比度")
                        mouth_mask = cv2.normalize(mouth_mask, None, 0, 255, cv2.NORM_MINMAX)
            else:
                if self.verbose:
                    print("警告: 未检测到嘴部区域，将使用全图混合")
                mouth_mask = None
            
            # 生成帧
            previous_frame = None  # 用于帧间平滑
            
            print("正在生成动画帧...")
            for i in range(total_frames):
                amplitude = smoothed_amplitudes[i]
                
                # 使用基础图像创建新帧
                if previous_frame is None:
                    frame = self.base_image.copy()
                else:
                    # 使用前一帧作为基础，减少闪烁
                    frame = previous_frame.copy()
                
                # 如果检测到嘴唇区域，则只修改嘴唇区域
                if hasattr(self, 'mouth_region') and self.mouth_region:
                    min_x, min_y, max_x, max_y = self.mouth_region
                    
                    # 动态混合两个图像的嘴唇区域，实现平滑过渡
                    # 将阈值调高，确保小振幅不会导致嘴巴张开
                    if amplitude > threshold:
                        # 只有超过阈值才开始张嘴
                        alpha = min(1.0, (amplitude - threshold) / (0.25 - threshold))  # 更自然的映射
                    else:
                        alpha = 0  # 低于阈值时嘴巴完全闭合
                        
                    alpha = max(0, min(0.9, alpha))  # 限制最大开口程度
                    
                    # 确保嘴巴在应该张开的时候是张开的，特别是一个词的开始
                    if i > 1 and i < total_frames - 1:
                        # 检测振幅上升
                        if amplitude > smoothed_amplitudes[i-1] * 1.5 and amplitude > threshold * 1.2:
                            alpha = max(alpha, 0.6)  # 确保快速上升时嘴巴充分张开
                    
                    if alpha > 0.01:  # 降低最小变化阈值，使细微的声音也有反应
                        # 获取嘴唇区域
                        base_mouth = self.base_image[min_y:max_y, min_x:max_x].copy()
                        open_mouth = self.open_image[min_y:max_y, min_x:max_x].copy()
                        
                        # 使用遮罩创建精确混合
                        weight_mask = mouth_mask.astype(np.float32) / 255.0
                        
                        # 创建动态权重掩码，强度由声音振幅决定
                        dynamic_weight = weight_mask * alpha
                        
                        # 使用更精细的图像混合
                        blended_mouth = np.zeros_like(base_mouth)
                        
                        for c in range(3):
                            base_channel = base_mouth[:, :, c].astype(np.float32)
                            open_channel = open_mouth[:, :, c].astype(np.float32)
                            
                            # 基于权重掩码的平滑混合
                            blended_channel = (1 - dynamic_weight) * base_channel + dynamic_weight * open_channel
                            blended_mouth[:, :, c] = blended_channel.astype(np.uint8)
                        
                        # 将混合后的嘴唇区域放回到图像中
                        frame[min_y:max_y, min_x:max_x] = blended_mouth
                        
                        # 存储当前帧用于下一帧的基础
                        previous_frame = frame.copy()
                else:
                    # 如果未检测到嘴唇区域，则根据振幅在两个图像之间混合
                    if amplitude > threshold:
                        alpha = min(0.8, (amplitude - threshold) / (0.25 - threshold))
                    else:
                        alpha = 0
                    
                    if alpha > 0.01:  # 降低最小变化阈值
                        frame = cv2.addWeighted(self.base_image, 1 - alpha, self.open_image, alpha, 0)
                        previous_frame = frame.copy()
                
                # 不添加振幅指示条
                self.frames.append(frame)
                
                # 显示进度
                if self.verbose or i % 200 == 0 or i == total_frames - 1:
                    print(f"进度: {(i+1)/total_frames*100:.1f}%", end="\r")
            
            print("\n动画帧生成完毕")
                
        except ImportError as e:
            print(f"警告: 缺少必要的库 ({e})。使用随机动画代替。")
            self.create_random_animation()
        except Exception as e:
            print(f"处理音频时出错: {e}")
            import traceback
            traceback.print_exc()
            self.create_random_animation()
    
    def create_random_animation(self):
        """创建随机嘴巴开合动画"""
        print("创建随机嘴部动画")
        
        total_frames = int(self.duration * self.fps)
        self.frames = []
        
        # 预先计算唇形区域掩码
        if self.mouth_region:
            min_x, min_y, max_x, max_y = self.mouth_region
            
            # 获取嘴唇区域
            base_mouth = self.base_image[min_y:max_y, min_x:max_x]
            open_mouth = self.open_image[min_y:max_y, min_x:max_x]
            
            # 计算RGB差异掩码
            diff_mask = np.zeros_like(base_mouth[:,:,0])
            
            # 累加三个通道的差异，提高精度
            for c in range(3):
                # 计算每个通道的差异
                channel_diff = cv2.absdiff(base_mouth[:,:,c], open_mouth[:,:,c])
                diff_mask = cv2.add(diff_mask, channel_diff)
            
            # 提取嘴唇变化区域
            _, lip_mask = cv2.threshold(diff_mask, 25, 255, cv2.THRESH_BINARY)
            
            # 使用中等大小的核进行膨胀，扩展嘴唇区域
            kernel = np.ones((2, 2), np.uint8)
            lip_mask = cv2.dilate(lip_mask, kernel, iterations=1)
            
            # 生成动态掩码，适应不同的嘴部变化
            h, w = lip_mask.shape
            dynamic_mask = np.zeros_like(lip_mask, dtype=np.float32)
            
            # 计算嘴唇区域中心
            lip_pixels = np.where(lip_mask > 0)
            if len(lip_pixels[0]) > 0:
                # 计算嘴唇区域中心
                center_y = int(np.mean(lip_pixels[0]))
                # 将中心点稍微下移，更接近下巴
                center_y = min(h-1, int(center_y * 1.1))
                
                # 创建从中心点向外的径向渐变
                for y in range(h):
                    for x in range(w):
                        # 计算到中心的距离
                        distance = np.sqrt((y - center_y)**2 + (x - w//2)**2)
                        # 最大半径为区域高度的一半
                        max_radius = h * 0.7
                        if distance < max_radius:
                            # 根据距离创建平滑衰减
                            weight = 1.0 - (distance / max_radius)**2
                            # 强调下巴区域的权重
                            if y > center_y:
                                # 下巴区域权重衰减较慢
                                weight = min(1.0, weight * 1.5)
                            dynamic_mask[y, x] = weight * 255
                        
            # 组合动态掩码和嘴唇掩码
            combined_mask = np.maximum(lip_mask.astype(np.float32), dynamic_mask * 0.4)
            final_mask = np.clip(combined_mask, 0, 255).astype(np.uint8)
            
            # 应用高斯模糊使边缘更平滑
            mouth_mask = cv2.GaussianBlur(final_mask, (5, 5), 0)
        
        # 使用周期性函数使开合更自然
        previous_frame = None  # 用于帧间平滑
        
        for i in range(total_frames):
            t = i / self.fps
            
            # 基础周期 (每秒约开合2次)
            base_cycle = 0.5 * (1 + math.sin(t * 2 * math.pi))
            
            # 加入随机变化
            random_factor = np.random.rand() * 0.2
            
            # 确保有足够的闭嘴时间
            if base_cycle < 0.3:
                blend_factor = 0  # 完全闭嘴
            else:
                blend_factor = min(0.75, base_cycle + random_factor - 0.3)
            
            # 创建新帧
            if previous_frame is None:
                frame = self.base_image.copy()
            else:
                # 使用前一帧作为基础，减少闪烁
                frame = previous_frame.copy()
            
            # 如果检测到嘴唇区域，则只修改嘴唇区域
            if self.mouth_region and blend_factor > 0.03:  # 降低最小变化阈值
                min_x, min_y, max_x, max_y = self.mouth_region
                
                # 获取嘴唇区域
                base_mouth = self.base_image[min_y:max_y, min_x:max_x].copy()
                open_mouth = self.open_image[min_y:max_y, min_x:max_x].copy()
                
                # 使用遮罩创建精确混合
                weight_mask = mouth_mask.astype(np.float32) / 255.0
                
                # 创建动态权重掩码，强度由声音振幅决定
                dynamic_weight = weight_mask * blend_factor
                
                # 基于距离的平滑过渡
                for y in range(dynamic_weight.shape[0]):
                    for x in range(dynamic_weight.shape[1]):
                        # 增强下巴区域的过渡平滑度
                        if y > dynamic_weight.shape[0] // 2:
                            # 下巴区域过渡更平滑
                            dynamic_weight[y, x] *= 0.6 + 0.4 * ((dynamic_weight.shape[0] - y) / (dynamic_weight.shape[0] // 2))
                
                # 使用更精细的图像混合
                blended_mouth = np.zeros_like(base_mouth)
                
                for c in range(3):
                    base_channel = base_mouth[:, :, c].astype(np.float32)
                    open_channel = open_mouth[:, :, c].astype(np.float32)
                    
                    # 基于权重掩码的平滑混合
                    blended_channel = (1 - dynamic_weight) * base_channel + dynamic_weight * open_channel
                    blended_mouth[:, :, c] = blended_channel.astype(np.uint8)
                
                # 减少边缘突变，创建更自然的过渡
                # 检测边缘
                edges = cv2.Canny(mouth_mask, 100, 200)
                # 扩展边缘区域
                kernel = np.ones((2, 2), np.uint8)
                edge_region = cv2.dilate(edges, kernel, iterations=1)
                
                # 创建边缘过渡掩码
                edge_mask = cv2.GaussianBlur(edge_region, (5, 5), 0)
                edge_weight = edge_mask.astype(np.float32) / 255.0
                
                # 在边缘处额外平滑
                for c in range(3):
                    blend_channel = blended_mouth[:, :, c].astype(np.float32)
                    base_channel = base_mouth[:, :, c].astype(np.float32)
                    
                    # 边缘处应用更多原图内容，增强自然感
                    edge_blend = edge_weight * 0.85  # 更高的边缘保留率
                    final_blend = (1 - edge_blend) * blend_channel + edge_blend * base_channel
                    blended_mouth[:, :, c] = final_blend.astype(np.uint8)
                
                # 将混合后的嘴唇区域放回到图像中
                frame[min_y:max_y, min_x:max_x] = blended_mouth
                
                # 存储当前帧用于下一帧的基础
                previous_frame = frame.copy()
            elif blend_factor > 0.03:
                # 如果未检测到嘴唇区域，则根据周期在两个图像之间混合
                frame = cv2.addWeighted(self.base_image, 1 - blend_factor, self.open_image, blend_factor, 0)
                previous_frame = frame.copy()
                
            self.frames.append(frame)
    
    def save_video(self):
        """保存动画为视频文件"""
        if not hasattr(self, 'frames') or not self.frames:
            print("没有帧可保存")
            return False
            
        print(f"保存视频到: {self.output_path}")
        
        # 获取视频尺寸
        h, w = self.frames[0].shape[:2]
        if self.verbose:
            print(f"视频尺寸: {w}x{h}, 总帧数: {len(self.frames)}")
        
        # 创建临时视频文件路径，而不是直接写入最终文件
        current_dir = os.path.dirname(os.path.abspath(self.output_path))
        if not current_dir:
            current_dir = os.getcwd()
            
        # 创建当前目录下的临时文件名
        temp_video_path = os.path.join(current_dir, f"_temp_video_{int(time_module.time())}.mp4")
        
        try:
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_video_path, fourcc, self.fps, (w, h))
            
            # 写入帧
            for i, frame in enumerate(self.frames):
                out.write(frame)
                if self.verbose or i % 300 == 0 or i == len(self.frames) - 1:
                    print(f"保存进度: {(i+1)/len(self.frames)*100:.1f}%", end="\r")
                
            out.release()
            print("\n视频帧写入完成")
        except Exception as e:
            print(f"保存视频帧时出错: {e}")
            import traceback
            traceback.print_exc()
            
            # 清理临时文件
            if os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except:
                    pass
                    
            return False
        
        # 如果有音频，添加到视频中
        if self.audio_path and os.path.exists(self.audio_path):
            try:
                import tempfile
                import subprocess
                import shutil
                
                print(f"开始添加音频: {self.audio_path}")
                
                # 创建临时音频文件
                temp_audio = os.path.join(current_dir, f"_temp_audio_{int(time_module.time())}.mp3")
                
                try:
                    print(f"预处理音频文件...")
                    result = subprocess.run([
                        'ffmpeg', '-i', self.audio_path, 
                        '-c:a', 'libmp3lame', '-y', temp_audio
                    ], capture_output=True)
                    
                    if result.returncode != 0:
                        print("预处理音频失败，使用原始音频文件")
                        processed_audio = self.audio_path
                    else:
                        print("预处理音频成功")
                        processed_audio = temp_audio
                        
                except Exception as e:
                    print(f"预处理音频出错: {e}")
                    processed_audio = self.audio_path
                
                try:
                    # 使用ffmpeg直接合并视频和音频，直接输出到最终文件
                    print("使用ffmpeg合并视频和音频...")
                    
                    cmd = [
                        'ffmpeg', 
                        '-i', temp_video_path,
                        '-i', processed_audio,
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-map', '0:v:0',
                        '-map', '1:a:0',
                        '-shortest',
                        '-y',  # 覆盖已存在的文件
                        self.output_path
                    ]
                    
                    # 执行命令
                    proc = subprocess.run(cmd, capture_output=True)
                    
                    if proc.returncode != 0:
                        error_msg = proc.stderr.decode('utf-8', errors='ignore')
                        print(f"FFmpeg错误: {error_msg}")
                        raise Exception("FFmpeg合并失败")
                    
                    print(f"已将音频添加到视频: {self.output_path}")
                        
                except Exception as inner_e:
                    print(f"处理音频和视频时出错: {inner_e}")
                    import traceback
                    traceback.print_exc()
                    
                    # 如果ffmpeg失败，尝试使用MoviePy
                    try:
                        from moviepy.editor import VideoFileClip, AudioFileClip
                        
                        print("尝试使用MoviePy添加音频...")
                        
                        # 加载视频
                        print("加载视频文件...")
                        video = VideoFileClip(temp_video_path)
                        
                        # 加载音频 - 使用处理过的音频文件
                        print("加载音频文件...")
                        audio = AudioFileClip(processed_audio)
                        
                        # 如果音频比视频长，截断音频
                        if audio.duration > video.duration:
                            print(f"音频时长({audio.duration}秒)大于视频时长({video.duration}秒)，截断音频")
                            audio = audio.subclip(0, video.duration)
                        
                        # 添加音频
                        print("添加音频到视频...")
                        final_video = video.set_audio(audio)
                        
                        # 保存最终视频
                        print(f"保存最终视频: {self.output_path}")
                        final_video.write_videofile(self.output_path, codec='libx264', audio_codec='aac', 
                                                  verbose=False, logger=None, ffmpeg_params=["-strict", "-2"])
                        
                        # 关闭文件
                        video.close()
                        audio.close()
                        final_video.close()
                        
                        print(f"已将音频添加到视频: {self.output_path}")
                    except Exception as moviepy_e:
                        print(f"MoviePy处理失败: {moviepy_e}")
                        print("保留无声视频")
                        
                        # 复制临时视频到最终输出
                        shutil.copy2(temp_video_path, self.output_path)
                
                # 清理临时文件
                finally:
                    # 删除临时视频和音频文件
                    if os.path.exists(temp_video_path):
                        try:
                            os.remove(temp_video_path)
                        except:
                            pass
                    
                    if os.path.exists(temp_audio):
                        try:
                            os.remove(temp_audio)
                        except:
                            pass
                    
            except ImportError as e:
                print(f"警告: 导入失败 ({e})。视频保存时没有音频。")
                # 直接复制临时视频到最终输出
                shutil.copy2(temp_video_path, self.output_path)
                
                # 删除临时视频
                if os.path.exists(temp_video_path):
                    try:
                        os.remove(temp_video_path)
                    except:
                        pass
                        
                return True
            except Exception as e:
                print(f"添加音频到视频时出错: {e}")
                import traceback
                traceback.print_exc()
                
                # 直接复制临时视频到最终输出
                shutil.copy2(temp_video_path, self.output_path)
                
                # 删除临时视频
                if os.path.exists(temp_video_path):
                    try:
                        os.remove(temp_video_path)
                    except:
                        pass
                        
                return True
        else:
            print("没有提供音频文件或文件不存在，保存无声视频")
            # 重命名临时视频为最终输出
            shutil.copy2(temp_video_path, self.output_path)
            
            # 删除临时视频
            if os.path.exists(temp_video_path):
                try:
                    os.remove(temp_video_path)
                except:
                    pass
        
        print(f"成功生成唇形动画视频: {self.output_path}")
        return True
        
    def generate(self):
        """生成说话视频的主函数"""
        # 第1步：加载图像
        self.load_images()
        
        # 第2步：生成说话动画
        self.generate_talking_animation()
        
        # 第3步：保存视频
        return self.save_video()

def main():
    parser = argparse.ArgumentParser(description="创建唇形动画，只改变图片的嘴部区域")
    parser.add_argument("base_image", help="基础图片路径（闭嘴状态）")
    parser.add_argument("open_mouth_image", help="张嘴图片路径")
    parser.add_argument("-a", "--audio", help="音频文件路径 (WAV, MP3等)")
    parser.add_argument("-o", "--output", help="输出视频路径")
    parser.add_argument("-d", "--duration", type=float, default=-1, 
                      help="视频时长（秒）（默认：使用音频时长，如果没有音频则为10秒）")
    parser.add_argument("--bg_color", nargs=3, type=int, default=[50, 50, 200], 
                      help="背景颜色 (B G R)（默认：50 50 200）")
    parser.add_argument("--fps", type=int, default=30, 
                      help="帧率（默认：30）")
    parser.add_argument("--smoothness", type=float, default=0.5,
                      help="嘴唇动画平滑度 (0-1)，越大越平滑（默认：0.5）")
    parser.add_argument("--verbose", action="store_true",
                      help="显示详细输出信息")
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.base_image):
        print(f"错误: 基础图片不存在: {args.base_image}")
        return 1
        
    if not os.path.exists(args.open_mouth_image):
        print(f"错误: 张嘴图片不存在: {args.open_mouth_image}")
        return 1
        
    if args.audio and not os.path.exists(args.audio):
        print(f"错误: 音频文件不存在: {args.audio}")
        return 1
    
    # 如果未指定持续时间且没有音频，使用默认值10秒
    duration = args.duration
    if duration <= 0 and args.audio is None:
        duration = 10
        
    try:
        # 创建生成器并生成视频
        generator = LipTalkingGenerator(
            args.base_image,
            args.open_mouth_image,
            args.audio,
            args.output,
            duration,
            tuple(args.bg_color),
            args.fps,
            args.smoothness
        )
        generator.verbose = args.verbose
        success = generator.generate()
        
        if success:
            print(f"\n成功生成唇形动画视频: {generator.output_path}")
            return 0
        else:
            print("生成视频失败")
            return 1
            
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    main() 