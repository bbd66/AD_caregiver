import cv2
import numpy as np
import argparse
import os
import time
import mediapipe as mp
import random
from moviepy.editor import VideoClip, VideoFileClip, AudioFileClip
from scipy.interpolate import interp1d
import tempfile

class DigitalHumanGenerator:
    def __init__(self, image_path, audio_path=None, output_path=None, 
                 duration=10, bg_color=(50, 50, 200), fps=30,
                 face_zoom=1.5, only_face=False):
        """
        从图像和音频创建数字人说话视频
        
        参数:
            image_path: 输入的人物图像路径
            audio_path: 音频文件路径（可选）
            output_path: 输出视频路径
            duration: 视频时长（秒）
            bg_color: 背景颜色 (B,G,R)
            fps: 帧率
            face_zoom: 人脸裁剪时的缩放因子
            only_face: 是否只保留面部，不保留肩部等
        """
        self.image_path = image_path
        self.audio_path = audio_path
        self.face_zoom = face_zoom
        self.only_face = only_face
        
        # 设置默认输出路径
        if output_path is None:
            base_name, _ = os.path.splitext(image_path)
            self.output_path = f"{base_name}_talking.mp4"
        else:
            self.output_path = output_path
            
        self.duration = duration
        self.bg_color = bg_color
        self.fps = fps
        
        # 创建临时文件路径用于存储裁剪后的图像
        _, self.cropped_image_path = tempfile.mkstemp(suffix='.jpg')
        
        # MediaPipe Face Mesh模型用于检测人脸关键点
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 嘴唇关键点索引
        self.lips_indices = [
            61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 
            291, 409, 270, 269, 267, 0, 37, 39, 40, 185
        ]
        
        # MediaPipe 人脸检测
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(
            min_detection_confidence=0.5
        )
    
    def __del__(self):
        """析构函数，清理临时文件"""
        try:
            if hasattr(self, 'cropped_image_path') and os.path.exists(self.cropped_image_path):
                os.remove(self.cropped_image_path)
        except:
            pass
    
    def crop_face_from_image(self):
        """
        从输入图像中检测并裁剪出人脸
        """
        print(f"Processing original image: {self.image_path}")
        
        # 读取原始图像
        image = cv2.imread(self.image_path)
        if image is None:
            raise ValueError(f"Could not read image: {self.image_path}")
        
        # 转换为RGB以进行人脸检测
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 使用MediaPipe进行人脸检测
        results = self.face_detection.process(image_rgb)
        
        if not results.detections:
            print("No face detected in the image. Using the original image.")
            self.cropped_image = image.copy()
            cv2.imwrite(self.cropped_image_path, self.cropped_image)
            return False
        
        # 获取最大的人脸边界框
        h, w = image.shape[:2]
        max_area = 0
        face_bbox = None
        
        for detection in results.detections:
            bbox = detection.location_data.relative_bounding_box
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            area = width * height
            if area > max_area:
                max_area = area
                face_bbox = (x, y, width, height)
        
        # 扩大人脸区域
        x, y, width, height = face_bbox
        face_center_x = x + width // 2
        face_center_y = y + height // 2
        
        # 扩大人脸区域的比例
        new_width = int(width * self.face_zoom)
        
        # 如果只要脸部，则高度和宽度相同
        if self.only_face:
            new_height = new_width
        else:
            # 否则，下方扩展更多以包含颈部和肩部
            new_height = int(height * (self.face_zoom + 1.0))
        
        # 计算新的边界框
        x1 = max(0, face_center_x - new_width // 2)
        y1 = max(0, face_center_y - new_height // 3)  # 上方留出较少空间
        x2 = min(w, face_center_x + new_width // 2)
        y2 = min(h, face_center_y + new_height * 2 // 3)  # 下方留出更多空间
        
        # 裁剪图像
        self.cropped_image = image[y1:y2, x1:x2]
        
        # 保存裁剪后的图像到临时文件
        cv2.imwrite(self.cropped_image_path, self.cropped_image)
        print(f"Face cropped and saved to temporary file: {self.cropped_image_path}")
        
        return True
    
    def load_cropped_image(self):
        """加载裁剪后的图像并检测面部特征点"""
        print(f"Loading cropped image for animation...")
        
        # 读取裁剪后的图像
        self.image = cv2.imread(self.cropped_image_path)
        if self.image is None:
            raise ValueError(f"Could not load cropped image")
            
        # 检测面部关键点
        image_rgb = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(image_rgb)
        
        self.face_landmarks = None
        if results.multi_face_landmarks:
            self.face_landmarks = results.multi_face_landmarks[0]
            self.extract_lip_points()
            return True
        else:
            print("Warning: No face landmarks detected in cropped image. Using basic animation.")
            return False
    
    def extract_lip_points(self):
        """从面部特征点提取嘴唇位置"""
        if self.face_landmarks is None:
            return
            
        h, w = self.image.shape[:2]
        self.original_lip_points = []
        
        for idx in self.lips_indices:
            pt = self.face_landmarks.landmark[idx]
            x, y = int(pt.x * w), int(pt.y * h)
            self.original_lip_points.append((x, y))
    
    def generate_talking_animation(self):
        """生成嘴唇动画序列"""
        if hasattr(self, 'original_lip_points') and self.original_lip_points:
            print("Generating mouth movement animation using detected lips")
            # 使用检测到的嘴唇关键点创建动画
            self.create_realistic_mouth_animation()
        else:
            print("Using basic mouth animation")
            # 如果没有检测到嘴唇，使用基础动画
            self.create_basic_animation()
    
    def create_realistic_mouth_animation(self):
        """基于真实嘴唇关键点创建动画"""
        # 如果有音频文件，使用音频振幅驱动嘴部动作
        if self.audio_path and os.path.exists(self.audio_path):
            self.create_audio_driven_animation()
        else:
            # 否则创建随机动画
            self.create_random_animation()
    
    def create_audio_driven_animation(self):
        """使用音频驱动嘴唇动画"""
        try:
            from pydub import AudioSegment
            
            print(f"Loading audio: {self.audio_path}")
            
            # 加载音频并获取振幅数据
            audio = AudioSegment.from_file(self.audio_path)
            audio_array = np.array(audio.get_array_of_samples())
            
            # 规范化音频数据
            normalized_audio = np.abs(audio_array) / np.max(np.abs(audio_array))
            
            # 计算音频时长（秒）
            audio_duration = len(audio_array) / audio.frame_rate
            
            # 如果未指定视频时长，使用音频时长
            if self.duration is None or self.duration <= 0:
                self.duration = audio_duration
                print(f"Using audio duration: {self.duration:.2f} seconds")
            
            # 创建时间点和对应的口型幅度
            total_frames = int(self.duration * self.fps)
            
            # 将音频振幅重采样到视频帧率
            audio_indices = np.linspace(0, len(normalized_audio) - 1, total_frames)
            
            # 创建动画帧
            self.frames = []
            for i in range(total_frames):
                # 获取当前帧对应的音频振幅
                audio_idx = int(audio_indices[i])
                if audio_idx < len(normalized_audio):
                    amplitude = normalized_audio[audio_idx]
                    # 应用平滑处理
                    start_idx = max(0, audio_idx - int(0.05 * audio.frame_rate))
                    end_idx = min(len(normalized_audio), audio_idx + int(0.05 * audio.frame_rate))
                    if end_idx > start_idx:
                        amplitude = np.mean(normalized_audio[start_idx:end_idx])
                else:
                    amplitude = 0
                
                # 调整振幅范围以增强嘴部动作
                amplitude = 0.2 + amplitude * 0.8
                    
                # 创建当前帧
                frame = self.create_frame(amplitude)
                self.frames.append(frame)
                
        except ImportError:
            print("Warning: pydub not installed. Using random animation instead.")
            self.create_random_animation()
        except Exception as e:
            print(f"Error processing audio: {e}")
            self.create_random_animation()
    
    def create_random_animation(self):
        """创建随机嘴唇动画"""
        print("Creating random mouth movement animation")
        
        total_frames = int(self.duration * self.fps)
        
        # 创建平滑的随机动作
        # 使用正弦波生成更自然的动作
        num_control_points = min(40, total_frames // 2)  # 更多控制点使动画更自然
        time_points = np.linspace(0, self.duration, num_control_points)
        random_values = np.random.rand(num_control_points) * 0.5 + 0.2
        
        # 添加一些语音暂停
        pauses = np.random.choice(range(num_control_points), size=int(num_control_points * 0.2), replace=False)
        for idx in pauses:
            random_values[idx] = 0.1
        
        # 插值函数
        interp_func = interp1d(time_points, random_values, kind='cubic')
        
        # 创建所有帧
        self.frames = []
        for i in range(total_frames):
            t = i / self.fps
            if t <= self.duration:
                # 获取当前口型振幅
                amplitude = interp_func(t) if t < time_points[-1] else random_values[-1]
                
                # 创建当前帧
                frame = self.create_frame(amplitude)
                self.frames.append(frame)
    
    def create_basic_animation(self):
        """创建基础嘴部动画（当没有检测到面部特征时）"""
        print("Creating basic mouth animation")
        
        # 获取图像大小
        h, w = self.image.shape[:2]
        
        # 估计嘴部位置（图像下半部分中心）
        mouth_center_x = w // 2
        mouth_center_y = int(h * 0.7)
        mouth_width = w // 4
        mouth_height = h // 10
        
        # 创建动画帧
        total_frames = int(self.duration * self.fps)
        self.frames = []
        
        # 生成随机口型变化
        time_points = np.linspace(0, self.duration, 20)
        random_values = np.random.rand(len(time_points)) * 0.5 + 0.2
        interp_func = interp1d(time_points, random_values, kind='cubic')
        
        for i in range(total_frames):
            t = i / self.fps
            if t <= self.duration:
                # 获取当前口型振幅
                amplitude = interp_func(t) if t < time_points[-1] else random_values[-1]
                
                # 复制原始图像
                frame = self.image.copy()
                
                # 创建纯色背景
                background = np.ones((h, w, 3), dtype=np.uint8)
                background[:] = self.bg_color
                
                # 将前景图像合成到背景上
                mask = np.zeros((h, w), dtype=np.uint8)
                cv2.circle(mask, (w//2, h//2), min(w,h)//2, 255, -1)  # 创建圆形遮罩
                cv2.copyTo(frame, mask, background)
                
                # 画一个代表嘴的椭圆
                mouth_h = int(mouth_height * (0.5 + amplitude))
                cv2.ellipse(background, 
                           (mouth_center_x, mouth_center_y),
                           (mouth_width, mouth_h),
                           0, 0, 360, (20, 20, 150), -1)
                
                self.frames.append(background)
    
    def create_frame(self, amplitude):
        """根据振幅创建一帧动画"""
        # 复制原始图像
        frame = self.image.copy()
        h, w = frame.shape[:2]
        
        # 创建纯色背景
        background = np.ones((h, w, 3), dtype=np.uint8)
        background[:] = self.bg_color
        
        # 将人物合成到背景上
        # 创建一个基本的人物遮罩
        mask = np.zeros((h, w), dtype=np.uint8)
        
        if hasattr(self, 'original_lip_points') and self.original_lip_points:
            # 如果有检测到面部特征，通过变形嘴唇来制作说话动画
            
            # 计算嘴唇中心
            lip_points = np.array(self.original_lip_points)
            lip_center_x = np.mean(lip_points[:, 0])
            lip_center_y = np.mean(lip_points[:, 1])
            
            # 根据振幅变形嘴唇关键点
            modified_lip_points = []
            for x, y in self.original_lip_points:
                # 上嘴唇点向上移动，下嘴唇点向下移动
                if y < lip_center_y:  # 上嘴唇
                    new_y = y - amplitude * 10
                else:  # 下嘴唇
                    new_y = y + amplitude * 10
                modified_lip_points.append((x, new_y))
                
            # 创建面部遮罩
            hull = cv2.convexHull(np.array([(int(x), int(y)) for x, y in modified_lip_points]))
            cv2.fillConvexPoly(mask, hull, 255)
            
            # 稍微扩大遮罩区域以包含整个面部
            mask = cv2.dilate(mask, np.ones((20, 20), np.uint8), iterations=10)
            
            # 将前景与背景合成
            cv2.copyTo(frame, mask, background)
            
            # 画变形后的嘴唇
            cv2.fillPoly(background, [np.array([(int(x), int(y)) for x, y in modified_lip_points])], (20, 20, 150))
        else:
            # 如果没有检测到面部特征，使用基本的圆形遮罩
            cv2.circle(mask, (w//2, h//2), min(w, h)//2, 255, -1)
            cv2.copyTo(frame, mask, background)
        
        return background
    
    def save_video(self):
        """保存动画为视频文件"""
        if not hasattr(self, 'frames') or not self.frames:
            print("No frames to save")
            return False
            
        print(f"Saving video to: {self.output_path}")
        
        # 获取视频尺寸
        h, w = self.frames[0].shape[:2]
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_path, fourcc, self.fps, (w, h))
        
        # 写入帧
        for frame in self.frames:
            out.write(frame)
            
        out.release()
        
        # 如果有音频，添加到视频中
        if self.audio_path and os.path.exists(self.audio_path):
            try:
                from moviepy.editor import VideoFileClip, AudioFileClip
                
                # 加载视频和音频
                video = VideoFileClip(self.output_path)
                audio = AudioFileClip(self.audio_path)
                
                # 如果音频比视频长，截断音频
                if audio.duration > video.duration:
                    audio = audio.subclip(0, video.duration)
                
                # 添加音频
                final_video = video.set_audio(audio)
                
                # 保存最终视频
                temp_output = self.output_path + ".temp.mp4"
                final_video.write_videofile(temp_output, codec='libx264')
                
                # 关闭文件
                video.close()
                audio.close()
                final_video.close()
                
                # 替换原视频
                os.replace(temp_output, self.output_path)
                print(f"Added audio to video: {self.output_path}")
                
            except ImportError:
                print("Warning: moviepy not installed. Video saved without audio.")
            except Exception as e:
                print(f"Error adding audio to video: {e}")
        
        print(f"Video saved successfully: {self.output_path}")
        return True
        
    def generate(self):
        """生成说话视频的主函数"""
        # 第1步：裁剪人脸
        self.crop_face_from_image()
        
        # 第2步：加载裁剪后的图像并检测面部特征
        self.load_cropped_image()
        
        # 第3步：生成说话动画
        self.generate_talking_animation()
        
        # 第4步：保存视频
        return self.save_video()

def main():
    parser = argparse.ArgumentParser(description="Generate a talking digital human video from an image and audio")
    parser.add_argument("image_path", help="Path to the original person image")
    parser.add_argument("-a", "--audio", help="Path to an audio file (WAV, MP3, etc.)")
    parser.add_argument("-o", "--output", help="Output video path")
    parser.add_argument("-d", "--duration", type=float, default=-1, 
                      help="Video duration in seconds (default: use audio duration if available, otherwise 10 seconds)")
    parser.add_argument("--bg_color", nargs=3, type=int, default=[50, 50, 200], 
                      help="Background color (B G R) (default: 50 50 200)")
    parser.add_argument("--fps", type=int, default=30, 
                      help="Frames per second (default: 30)")
    parser.add_argument("--face_zoom", type=float, default=1.5, 
                     help="Face zoom factor (default: 1.5)")
    parser.add_argument("--only_face", action="store_true", 
                     help="Crop only the face, not including neck and shoulders")
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.image_path):
        print(f"Error: Input image does not exist: {args.image_path}")
        return 1
        
    if args.audio and not os.path.exists(args.audio):
        print(f"Error: Audio file does not exist: {args.audio}")
        return 1
    
    # 如果未指定持续时间且没有音频，使用默认值10秒
    duration = args.duration
    if duration <= 0 and args.audio is None:
        duration = 10
        
    try:
        # 创建生成器并生成视频
        generator = DigitalHumanGenerator(
            args.image_path,
            args.audio,
            args.output,
            duration,
            tuple(args.bg_color),
            args.fps,
            args.face_zoom,
            args.only_face
        )
        success = generator.generate()
        
        if success:
            print(f"\n成功生成数字人视频: {generator.output_path}")
            return 0
        else:
            print("生成视频失败")
            return 1
            
    except Exception as e:
        print(f"错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 确保临时文件被清理
        pass

if __name__ == "__main__":
    main() 