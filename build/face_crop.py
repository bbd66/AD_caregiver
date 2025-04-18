import face_recognition
import cv2
import numpy as np
import argparse
import os

def detect_and_crop_person(image_path, output_path=None, target_ratio=None):
    """
    使用face_recognition库检测图像中的人脸并裁剪
    
    参数:
        image_path: 输入图像路径
        output_path: 输出图像路径，如果为None则使用原文件名加_cropped后缀
        target_ratio: 目标宽高比，如果为None则保持原始比例
    
    返回:
        裁剪后的图像路径
    """
    # 读取图像 (使用cv2读取以便后续处理)
    img = cv2.imread(image_path)
    if img is None:
        raise Exception(f"无法读取图像: {image_path}")
    
    # 转换为RGB (face_recognition需要RGB图像)
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # 检测人脸位置
    face_locations = face_recognition.face_locations(rgb_img)
    
    if len(face_locations) == 0:
        print("未检测到人脸，将返回原始图像")
        cropped_img = img.copy()
    else:
        # 如果检测到多个人脸，选择最大的一个
        if len(face_locations) > 1:
            face_areas = [(bottom-top)*(right-left) for top, right, bottom, left in face_locations]
            max_face_idx = face_areas.index(max(face_areas))
            face_location = face_locations[max_face_idx]
        else:
            face_location = face_locations[0]
        
        # 解析人脸位置
        top, right, bottom, left = face_location
        
        # 扩展人脸区域以包含更多的身体部分
        face_height = bottom - top
        face_width = right - left
        face_center_x = (left + right) // 2
        face_center_y = (top + bottom) // 2
        
        # 水平扩展
        width_expansion = 2.0
        new_width = int(face_width * width_expansion)
        new_left = max(0, face_center_x - new_width // 2)
        new_right = min(img.shape[1], face_center_x + new_width // 2)
        
        # 垂直扩展 (上部稍微扩展，下部更多扩展以包含身体)
        top_expansion = 1.0  # 向上扩展的因子
        bottom_expansion = 3.0  # 向下扩展的因子
        
        new_top = max(0, int(top - face_height * top_expansion))
        new_bottom = min(img.shape[0], int(bottom + face_height * bottom_expansion))
        
        # 裁剪图像
        try:
            cropped_img = img[new_top:new_bottom, new_left:new_right]
            
            # 检查裁剪是否成功
            if cropped_img.size == 0:
                print("警告: 裁剪后图像为空，将使用原始图像")
                cropped_img = img.copy()
        except Exception as e:
            print(f"裁剪失败: {str(e)}, 将使用原始图像")
            cropped_img = img.copy()
    
    # 如果指定了目标比例，调整裁剪区域
    if target_ratio is not None and cropped_img.shape[0] > 0 and cropped_img.shape[1] > 0:
        current_ratio = cropped_img.shape[1] / cropped_img.shape[0]  # 宽/高
        
        if current_ratio > target_ratio:
            # 过宽，需要剪掉两侧
            new_width = int(cropped_img.shape[0] * target_ratio)
            if new_width > 0:
                start = (cropped_img.shape[1] - new_width) // 2
                cropped_img = cropped_img[:, start:start+new_width]
        else:
            # 过高，需要剪掉上下
            new_height = int(cropped_img.shape[1] / target_ratio)
            if new_height > 0:
                start = (cropped_img.shape[0] - new_height) // 2
                cropped_img = cropped_img[start:start+new_height, :]
    
    # 保存结果
    if output_path is None:
        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_cropped{ext}"
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 保存前确认图像不为空
    if cropped_img.size > 0:
        cv2.imwrite(output_path, cropped_img)
        return output_path
    else:
        raise Exception("无法保存图像：处理后的图像为空")

def main():
    parser = argparse.ArgumentParser(description="检测并裁剪图像中的人物")
    parser.add_argument("input_path", help="输入图像路径")
    parser.add_argument("-o", "--output", help="输出图像路径")
    parser.add_argument("-r", "--ratio", type=float, help="目标宽高比，例如1.5表示宽度是高度的1.5倍")
    
    args = parser.parse_args()
    
    try:
        # 检查输入文件是否存在
        if not os.path.exists(args.input_path):
            print(f"错误: 输入文件不存在: {args.input_path}")
            return
            
        output_path = detect_and_crop_person(args.input_path, args.output, args.ratio)
        print(f"处理完成，已保存到: {output_path}")
    except Exception as e:
        print(f"错误: {str(e)}")

if __name__ == "__main__":
    main() 