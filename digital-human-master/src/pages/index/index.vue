<template>
  <view class="home-container" :style="{ backgroundColor: currentBgColor }">
    <!-- 顶部导航栏 -->
    <view class="header">
      <view class="header-left">
        <view class="app-logo">
          <image src="/src/static/logo.png" mode="aspectFit" class="logo-image"></image>
        </view>
      </view>
      <view class="header-center">
        <text class="header-title">家人聊天</text>
      </view>
      <view class="header-right">
        <view class="icon-wrapper" @tap="onHelp">
          <uni-icons type="help" size="24" color="#333"></uni-icons>
        </view>
        <view class="icon-wrapper" @tap="goToProfile">
          <uni-icons type="person" size="24" color="#333"></uni-icons>
        </view>
        <view class="icon-wrapper" @tap="onSettings">
          <uni-icons type="gear" size="24" color="#333"></uni-icons>
        </view>
      </view>
    </view>

    <!-- 中央内容区 -->
  <view class="content">
      <!-- 数字人形象区域 -->
      <view class="avatar-area">
        <view v-if="digitalHumans.length === 0" class="empty-digital-human">
          <image src="/src/static/logo.png" mode="aspectFit" class="empty-image"></image>
          <text class="empty-text">暂无数字人</text>
          <view class="add-btn" @tap="goToManagePage">
            <uni-icons type="plusempty" size="20" color="#fff"></uni-icons>
            <text>添加数字人</text>
          </view>
        </view>
        <view v-else class="avatar-placeholder">
          <!-- 音频播放时显示GIF，否则显示静态图片 -->
          <image 
            v-if="isPlayingAudio" 
            src="/src/static/digital_human.gif" 
            mode="aspectFit" 
            class="avatar-image">
          </image>
          <image 
            v-else-if="digitalHumans && digitalHumans.length > 0 && 
                      currentDigitalHumanIndex.value >= 0 && 
                      currentDigitalHumanIndex.value < digitalHumans.length && 
                      digitalHumans[currentDigitalHumanIndex.value].avatar" 
            :src="digitalHumans[currentDigitalHumanIndex.value].avatar" 
            mode="aspectFit" 
            class="avatar-image">
          </image>
          <!-- 没有数字人头像时显示默认静态图片 -->
          <image 
            v-else
            src="/src/static/digital_human.jpg" 
            mode="aspectFit" 
            class="avatar-image">
          </image>
          
          <!-- 数字人名称显示 -->
          <view class="digital-human-name" v-if="digitalHumans && digitalHumans.length > 0 && currentDigitalHumanIndex.value >= 0 && currentDigitalHumanIndex.value < digitalHumans.length">
            <text>{{ digitalHumans[currentDigitalHumanIndex.value].name }}</text>
            <view class="training-badge" :class="{
              'untrained': digitalHumans[currentDigitalHumanIndex.value].training_status === 'untrained',
              'training': digitalHumans[currentDigitalHumanIndex.value].training_status === 'training',
              'trained': digitalHumans[currentDigitalHumanIndex.value].training_status === 'trained'
            }">
              {{ digitalHumans[currentDigitalHumanIndex.value].training_status === 'untrained' ? '未训练' : 
                 digitalHumans[currentDigitalHumanIndex.value].training_status === 'training' ? '训练中' : '已训练' }}
            </view>
          </view>
        </view>
      </view>

      <!-- 语音交互提示区域 -->
      <view class="interaction-area">
        <view class="interaction-text">{{ interactionText }}</view>
        
        <!-- 录音波形动画 (仅在录音时显示) -->
        <view class="waveform" v-if="isRecording">
          <view class="wave-bar" v-for="(height, index) in waveHeights" :key="index" 
                :style="{ height: height + 'rpx' }"></view>
        </view>
      </view>
      
      <!-- 功能按钮区域 -->
      <view class="function-buttons">
        <view class="button-row">
          <!-- 数字人管理按钮 -->
          <view class="function-button digital-human-manage" @tap="goToManagePage">
            <uni-icons type="gear-filled" size="32" color="#333"></uni-icons>
            <text class="button-label">管理家人</text>
          </view>
          
          <!-- 数字人切换按钮 -->
          <view class="function-button digital-human-toggle" 
                :class="{ 'expanded': isDigitalHumanExpanded, 'disabled': digitalHumans.length === 0 }" 
                @tap="handleDigitalHumanToggle">
            <uni-icons type="staff" size="32" :color="digitalHumans.length > 0 ? '#333' : '#999'"></uni-icons>
            <text class="button-label">切换家人</text>
          </view>
        </view>
        
        <view class="button-row">
          <!-- 背景色切换按钮 -->
          <view class="function-button theme-toggle" :class="{ 'expanded': isThemeExpanded }" @tap="toggleThemeExpanded">
            <uni-icons type="color" size="32" color="#333"></uni-icons>
            <text class="button-label">更换背景</text>
          </view>
          
          <!-- 刷新按钮 -->
          <view class="function-button refresh-button" @tap="reloadPage">
            <uni-icons type="refresh" size="32" color="#333"></uni-icons>
            <text class="button-label">刷新数据</text>
          </view>
        </view>
      </view>
      
      <!-- 数字人选择浮层 -->
      <view class="digital-human-popup" v-if="isDigitalHumanExpanded">
        <view class="popup-header">
          <text class="popup-title">选择家人</text>
          <view class="popup-close" @tap="closeDigitalHumanPopup">
            <uni-icons type="close" size="20" color="#666"></uni-icons>
          </view>
        </view>
        <view v-if="digitalHumans.length > 0" class="digital-human-grid">
          <view 
            v-for="(item, index) in digitalHumans" 
            :key="index" 
            class="digital-human-card"
            :class="{ 'active': index === currentDigitalHumanIndex.value }"
            @tap="switchDigitalHuman(index)"
          >
            <image :src="item.avatar || '/src/static/logo.png'" mode="aspectFill" class="digital-human-portrait"></image>
            <view class="digital-human-info">
              <text class="digital-human-name-text">{{ item.name || '数字人' + (index + 1) }}</text>
              <text class="digital-human-desc">{{ item.description || '数字人助手' }}</text>
              <view class="card-badge" :class="{
                'untrained': item.training_status === 'untrained',
                'training': item.training_status === 'training',
                'trained': item.training_status === 'trained'
              }">
                {{ item.training_status === 'untrained' ? '未训练' : 
                   item.training_status === 'training' ? '训练中' : '已训练' }}
              </view>
            </view>
          </view>
        </view>
        <view v-else class="empty-popup-state">
          <image src="/src/static/logo.png" mode="aspectFit" class="empty-image-small"></image>
          <text class="empty-text">暂无数字人，请先添加</text>
          <view class="add-btn-small" @tap="goToManagePage">
            <uni-icons type="plusempty" size="16" color="#fff"></uni-icons>
            <text>前往添加</text>
          </view>
        </view>
      </view>
      
      <!-- 背景色切换浮层 -->
      <view class="theme-colors" v-if="isThemeExpanded">
        <view 
          v-for="(color, index) in bgColors" 
          :key="index" 
          class="color-option"
          :style="{ backgroundColor: color }"
          :class="{ 'active': currentBgColor === color }"
          @tap="changeBgColor(color)"
        ></view>
      </view>
    </view>

    <!-- 底部操作栏 -->
    <view class="footer">
      <view class="footer-buttons">
        <view class="voice-button-container">
          <view 
            class="voice-button" 
            :class="{ 'recording': isRecording, 'disabled': digitalHumans.length === 0 }"
            @touchstart="startRecording" 
            @touchend="stopRecording"
            @touchmove="checkCancelRecording"
          >
            <uni-icons :type="isRecording ? 'mic-filled' : 'mic'" size="32" color="#fff"></uni-icons>
            <view class="cancel-area" v-if="isRecording">
              <text>↑ 上滑取消</text>
            </view>
          </view>
        </view>
        
        <!-- 通话按钮 -->
        <view class="call-button-container">
          <view class="call-button" :class="{ 'disabled': digitalHumans.length === 0 }" @tap="callDigitalHuman">
            <uni-icons type="phone" size="32" color="#fff"></uni-icons>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { digitalHumanService, fileUploadService } from '@/services/api.js'

// API基础URL和API前缀
const API_BASE_URL = 'http://localhost:8000'; // 与api.js中保持一致
const DIGITAL_API_PREFIX = '/api/v1/digital'; // 与api.js中保持一致
const FILES_API_PREFIX = '/api/v1/files'; // 与api.js中保持一致

// 录音管理器
let recorderManager = null;
// Web Audio API 相关变量
let audioContext = null;
let mediaRecorder = null;
let audioChunks = [];
// 录音文件路径
const audioFilePath = ref('');
// 录音计时器
let recordTimer = null;
// 录音时长（秒）
const recordDuration = ref(0);

// 初始化录音管理器
const initRecorder = () => {
  // #ifdef H5
  // H5环境使用 Web Audio API
  try {
    // 检查浏览器是否支持 MediaRecorder API
    if (typeof MediaRecorder === 'undefined') {
      console.error('您的浏览器不支持 MediaRecorder API');
      uni.showToast({
        title: '当前浏览器不支持录音功能',
        icon: 'none'
      });
      return;
    }
    
    console.log('H5环境: 使用Web Audio API初始化录音');
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    console.log('音频上下文创建成功');
    return;
  } catch (error) {
    console.error('H5环境: 初始化录音功能失败:', error);
    uni.showToast({
      title: '录音功能不可用',
      icon: 'none'
    });
    return;
  }
  // #endif
  
  // #ifndef H5
  // 非H5环境使用 uni.getRecorderManager
  try {
    recorderManager = uni.getRecorderManager();
    
    if (!recorderManager) {
      console.error('录音管理器创建失败');
      uni.showToast({
        title: '录音功能不可用',
        icon: 'none'
      });
      return;
    }
    
    // 监听录音开始事件
    recorderManager.onStart(() => {
      console.log('录音开始');
      // 开始计时
      recordTimer = setInterval(() => {
        recordDuration.value++;
      }, 1000);
    });
    
    // 监听录音结束事件
    recorderManager.onStop(async (res) => {
      console.log('录音结束', res);
      clearInterval(recordTimer);
      
      // 保存录音文件路径
      audioFilePath.value = res.tempFilePath;
      
      // 显示录音时长
      const duration = Math.round(res.duration / 1000); // 转换为秒
      
      // 如果不是取消录音，则处理录音文件
      if (isRecording.value === false && audioFilePath.value) {
        interactionText.value = `录音已完成 (${duration}秒)，正在上传...`;
        
        try {
          console.log('开始上传录音文件:', audioFilePath.value);
          
          // 上传录音文件
          const uploadResult = await fileUploadService.uploadRecordedAudio(audioFilePath.value);
          console.log('上传结果:', uploadResult);
          
          if (uploadResult.success) {
            // 上传成功，显示音频URL
            console.log('录音上传成功，URL:', uploadResult.audioUrl);
            interactionText.value = '录音上传成功，正在生成回复...';
            
            // 获取当前选中的数字人ID
            const currentDigitalHuman = digitalHumans[currentDigitalHumanIndex.value];
            if (!currentDigitalHuman) {
              throw new Error('未找到选中的数字人');
            }
            
            // 调用生成语音 API
            console.log('开始生成语音，数字人ID:', currentDigitalHuman.id, '音频URL:', uploadResult.audioUrl);
            const generateResult = await digitalHumanService.generateVoice(
              currentDigitalHuman.id,
              uploadResult.audioUrl
            );
            
            if (generateResult.success) {
              console.log('语音生成成功，URL:', generateResult.audioUrl);
              interactionText.value = '语音生成成功';
              
              // 播放生成的语音
              await playAudio(generateResult.audioUrl);
            } else {
              throw new Error(generateResult.message || '生成语音失败');
            }
          } else {
            // 上传失败
            console.error('录音上传失败:', uploadResult.message);
            interactionText.value = '录音上传失败';
            
            // 显示错误提示
            uni.showToast({
              title: uploadResult.message || '上传失败',
              icon: 'none'
            });
          }
        } catch (error) {
          console.error('处理录音文件时出错:', error);
          interactionText.value = '处理录音失败';
          
          // 显示错误提示
          uni.showToast({
            title: error.message || '处理录音失败',
            icon: 'none'
          });
        } finally {
          // 关闭已使用的媒体流
          stream.getTracks().forEach(track => track.stop());
        }
      }
    });
    
    // 监听录音错误事件
    recorderManager.onError((err) => {
      console.error('录音错误:', err);
      uni.showToast({
        title: '录音失败: ' + err.errMsg,
        icon: 'none'
      });
      isRecording.value = false;
      interactionText.value = '录音失败，请重试';
      stopWaveformAnimation();
    });
    
    console.log('录音管理器初始化成功');
  } catch (error) {
    console.error('初始化录音管理器失败:', error);
    recorderManager = null;
  }
  // #endif
};

// 预览录音（播放）
const previewRecording = () => {
  if (!audioFilePath.value) {
    uni.showToast({
      title: '没有录音文件',
      icon: 'none'
    });
    return;
  }
  
  // 创建内部音频上下文
  const innerAudioContext = uni.createInnerAudioContext();
  innerAudioContext.src = audioFilePath.value;
  innerAudioContext.autoplay = true;
  
  // 显示正在播放
  interactionText.value = '正在播放录音...';
  
  // 设置为播放状态，显示视频
  isPlayingAudio.value = true;
  
  // 监听播放结束
  innerAudioContext.onEnded(() => {
    innerAudioContext.destroy();
    interactionText.value = '录音播放完成';
    
    // 播放结束，恢复显示图片
    isPlayingAudio.value = false;
    
    // 3秒后恢复默认提示
    setTimeout(() => {
      interactionText.value = '按住按钮开始语音对话';
    }, 3000);
  });
  
  // 监听错误
  innerAudioContext.onError((err) => {
    console.error('播放录音错误:', err);
    innerAudioContext.destroy();
    uni.showToast({
      title: '播放录音失败',
      icon: 'none'
    });
    interactionText.value = '按住按钮开始语音对话';
    
    // 错误时也恢复显示图片
    isPlayingAudio.value = false;
  });
};

// 结束录音并发送
const stopRecording = (e) => {
  if (!isRecording.value) return;
  
  isRecording.value = false;
  interactionText.value = '录音已完成，正在处理...';
  stopWaveformAnimation();
  
  // 重置触摸起始位置
  touchStartY.value = 0;
  
  // H5环境处理
  // #ifdef H5
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    try {
      mediaRecorder.stop();
    } catch (error) {
      console.error('H5停止录音失败:', error);
      interactionText.value = '录音失败，请重试';
    }
  } else {
    interactionText.value = '录音功能不可用';
    uni.showToast({
      title: '录音功能不可用',
      icon: 'none'
    });
  }
  return;
  // #endif
  
  // 非H5环境处理
  // #ifndef H5
  // 停止录音
  if (recorderManager) {
    try {
      recorderManager.stop();
    } catch (error) {
      console.error('停止录音失败:', error);
      interactionText.value = '录音失败，请重试';
      uni.showToast({
        title: '录音功能异常',
        icon: 'none'
      });
    }
  } else {
    console.error('录音管理器不存在');
    interactionText.value = '录音功能不可用';
    uni.showToast({
      title: '录音功能不可用',
      icon: 'none'
    });
  }
  // #endif
};

// 检查是否上滑取消
const checkCancelRecording = (e) => {
  if (!isRecording.value) return;
  
  try {
    // 获取触摸点位置
    const touch = e.touches[0];
    
    // 记录起始触摸位置（如果没有记录过）
    if (!touchStartY.value) {
      touchStartY.value = touch.clientY;
      return;
    }
    
    // 计算移动距离
    const moveDistance = touchStartY.value - touch.clientY;
    
    // 如果向上移动超过50像素，则取消录音
    if (moveDistance > 50) {
      isRecording.value = false;
      interactionText.value = '录音已取消';
      stopWaveformAnimation();
      
      // 重置触摸起始位置
      touchStartY.value = 0;
      
      // H5环境处理
      // #ifdef H5
      if (mediaRecorder && mediaRecorder.state === 'recording') {
        try {
          // 在H5中取消时，停止mediaRecorder但不处理录音数据
          mediaRecorder.stop();
          // 清空录音数据
          audioChunks = [];
          audioFilePath.value = '';
          // 取消计时
          clearInterval(recordTimer);
        } catch (error) {
          console.error('H5取消录音失败:', error);
        }
      }
      // #endif
      
      // 非H5环境取消录音
      // #ifndef H5
      // 取消录音
      if (recorderManager) {
        try {
          recorderManager.stop();
          audioFilePath.value = ''; // 清空录音文件路径
        } catch (error) {
          console.error('取消录音失败:', error);
        }
      }
      // #endif
      
      // 重置提示文本
      setTimeout(() => {
        interactionText.value = '按住按钮开始语音对话';
      }, 1500);
    }
  } catch (error) {
    console.error('检查滑动取消录音时出错:', error);
  }
};

// 交互提示文本
const interactionText = ref('按住按钮开始语音对话')

// 录音状态
const isRecording = ref(false)

// 音频播放状态（控制显示视频还是图片）
const isPlayingAudio = ref(false)

// 记录触摸起始位置
const touchStartY = ref(0)

// 波形高度数据 (用于动画)
const waveHeights = reactive(Array(16).fill(10))

// 数字人数据
const digitalHumans = reactive([])

// 当前选中的数字人索引
const currentDigitalHumanIndex = ref(0)

// 加载状态
const loading = ref(false)

// 分页参数
const pagination = reactive({
  skip: 0,
  limit: 20, // 主页加载更多数据
  total: 0
})

// 数字人选择器是否展开
const isDigitalHumanExpanded = ref(false)

// 数字人选择变化监听
const onDigitalHumanChange = (human) => {
  currentDigitalHumanIndex.value = digitalHumans.findIndex(item => item.id === human.id)
  // 存储当前选择的数字人ID
  try {
    uni.setStorageSync('currentDigitalHumanId', human.id)
  } catch (e) {
    console.error('保存当前数字人ID失败:', e)
  }
  // 隐藏选择器
  isDigitalHumanExpanded.value = false
}

// 修复数字人切换函数
const switchDigitalHuman = (index) => {
  if (digitalHumans && digitalHumans.length > 0 && 
      index >= 0 && index < digitalHumans.length) {
    currentDigitalHumanIndex.value = index
    
    // 保存用户选择的数字人id
    try {
      // 存储当前选择的数字人ID而不是索引，这样即使列表变化也能找到同一个数字人
      const selectedId = digitalHumans[index].id
      uni.setStorageSync('currentDigitalHumanId', selectedId)
      console.log('保存数字人选择:', selectedId)
    } catch (e) {
      console.error('保存数字人选择失败:', e)
    }
    
    // 显示提示信息
    uni.showToast({
      title: `已切换到${digitalHumans[index].name}`,
      icon: 'none',
      duration: 1500
    })
    
    // 更新交互提示文本
    interactionText.value = `${digitalHumans[index].name}已准备好，按住按钮开始对话`
    
    // 关闭选择器
    isDigitalHumanExpanded.value = false
    
    // 3秒后恢复默认提示文本
    setTimeout(() => {
      interactionText.value = '按住按钮开始语音对话'
    }, 3000)
  }
}

// 波形动画定时器
let waveformInterval = null

// 背景颜色设置
const bgColors = [
  '#f5f7fa', // 默认浅灰色
  '#e8f4f8', // 浅蓝色
  '#f0f8ed', // 浅绿色
  '#faf4f0', // 浅橙色
  '#f8f0f8', // 浅紫色
  '#fffaeb'  // 浅黄色
]

// 当前背景颜色
const currentBgColor = ref(bgColors[0])

// 是否展开主题选择器
const isThemeExpanded = ref(false)

// 展开/收起主题选择器
const toggleThemeExpanded = () => {
  isThemeExpanded.value = !isThemeExpanded.value
  
  // 如果展开主题选择器，则收起数字人选择器
  if (isThemeExpanded.value && isDigitalHumanExpanded.value) {
    isDigitalHumanExpanded.value = false
  }
}

// 更换背景颜色
const changeBgColor = (color) => {
  currentBgColor.value = color
  // 保存用户选择的颜色
  uni.setStorageSync('bgColor', color)
  
  // 关闭颜色选择器
  setTimeout(() => {
    isThemeExpanded.value = false
  }, 300)
}

// 模拟波形动画
const animateWaveform = () => {
  waveformInterval = setInterval(() => {
    for (let i = 0; i < waveHeights.length; i++) {
      // 生成20-60之间的随机高度
      waveHeights[i] = Math.floor(Math.random() * 40) + 20
    }
  }, 150)
}

// 停止波形动画
const stopWaveformAnimation = () => {
  if (waveformInterval) {
    clearInterval(waveformInterval)
    waveformInterval = null
  }
}

// 开始录音
const startRecording = (e) => {
  // 如果没有数字人，不允许录音
  if (digitalHumans.length === 0) {
    showNoDigitalHumanTip();
    return;
  }
  
  // 检查当前数字人是否已经训练完成
  if (digitalHumans[currentDigitalHumanIndex.value] && 
      digitalHumans[currentDigitalHumanIndex.value].training_status !== 'trained') {
    showNotTrainedTip();
    return;
  }
  
  // H5环境处理
  // #ifdef H5
  try {
    if (typeof MediaRecorder === 'undefined') {
      uni.showToast({
        title: '当前浏览器不支持录音功能',
        icon: 'none'
      });
      return;
    }
    
    // 请求麦克风权限
    navigator.mediaDevices.getUserMedia({ audio: true })
      .then(stream => {
        isRecording.value = true;
        recordDuration.value = 0;
        
        if (digitalHumans && digitalHumans.length > 0 && 
            currentDigitalHumanIndex.value >= 0 && 
            currentDigitalHumanIndex.value < digitalHumans.length) {
          const currentName = digitalHumans[currentDigitalHumanIndex.value].name;
          interactionText.value = `${currentName}正在聆听...`;
        } else {
          interactionText.value = '正在聆听...';
        }
        
        // 重置之前的录音数据
        audioChunks = [];
        
        // 创建 MediaRecorder，指定 MIME 类型为 audio/mp3
        const options = {
          mimeType: 'audio/mp3',
          audioBitsPerSecond: 128000
        };
        
        // 如果浏览器不支持 audio/mp3，则使用 audio/webm
        if (!MediaRecorder.isTypeSupported(options.mimeType)) {
          options.mimeType = 'audio/webm';
        }
        
        mediaRecorder = new MediaRecorder(stream, options);
        
        // 开始录音计时
        recordTimer = setInterval(() => {
          recordDuration.value++;
        }, 1000);
        
        // 收集录音数据
        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) {
            audioChunks.push(e.data);
          }
        };
        
        // 录音结束处理
        mediaRecorder.onstop = async () => {
          clearInterval(recordTimer);
          
          // 如果用户取消了录音
          if (isRecording.value) {
            // 此时可能是意外停止，不处理录音数据
            return;
          }
          
          try {
            // 将收集的数据块合并为一个Blob对象
            const audioBlob = new Blob(audioChunks, { type: options.mimeType });
            
            // 创建临时文件
            const fileName = `recorded_audio_${Date.now()}.${options.mimeType === 'audio/mp3' ? 'mp3' : 'webm'}`;
            const file = new File([audioBlob], fileName, { type: options.mimeType });
            
            // 显示录音时长
            const duration = recordDuration.value;
            interactionText.value = `录音已完成 (${duration}秒)，正在上传...`;
            
            console.log('开始上传录音文件:', file);
            
            // 上传录音文件
            const uploadResult = await fileUploadService.uploadRecordedAudio(file);
            console.log('上传结果:', uploadResult);
            
            if (uploadResult.success) {
              // 上传成功，显示音频URL
              console.log('录音上传成功，URL:', uploadResult.audioUrl);
              interactionText.value = '录音上传成功，正在生成回复...';
              
              // 获取当前选中的数字人ID
              const currentDigitalHuman = digitalHumans[currentDigitalHumanIndex.value];
              if (!currentDigitalHuman) {
                throw new Error('未找到选中的数字人');
              }
              
              // 调用生成语音 API
              console.log('开始生成语音，数字人ID:', currentDigitalHuman.id, '音频URL:', uploadResult.audioUrl);
              const generateResult = await digitalHumanService.generateVoice(
                currentDigitalHuman.id,
                uploadResult.audioUrl
              );
              
              if (generateResult.success) {
                console.log('语音生成成功，URL:', generateResult.audioUrl);
                interactionText.value = '语音生成成功';
                
                // 播放生成的语音
                await playAudio(generateResult.audioUrl);
              } else {
                throw new Error(generateResult.message || '生成语音失败');
              }
            } else {
              // 上传失败
              console.error('录音上传失败:', uploadResult.message);
              interactionText.value = '录音上传失败';
              
              // 显示错误提示
              uni.showToast({
                title: uploadResult.message || '上传失败',
                icon: 'none'
              });
            }
          } catch (error) {
            console.error('处理录音文件时出错:', error);
            interactionText.value = '处理录音失败';
            
            // 显示错误提示
            uni.showToast({
              title: error.message || '处理录音失败',
              icon: 'none'
            });
          } finally {
            // 关闭已使用的媒体流
            stream.getTracks().forEach(track => track.stop());
          }
        };
        
        // 处理录音错误
        mediaRecorder.onerror = (err) => {
          console.error('H5录音错误:', err);
          uni.showToast({
            title: '录音失败',
            icon: 'none'
          });
          isRecording.value = false;
          interactionText.value = '录音失败，请重试';
          stopWaveformAnimation();
        };
        
        // 开始录音
        mediaRecorder.start();
        animateWaveform();
        
        // 重置触摸起始位置
        touchStartY.value = 0;
      })
      .catch(err => {
        console.error('获取麦克风权限失败:', err);
        uni.showToast({
          title: '无法访问麦克风',
          icon: 'none'
        });
      });
    return;
  } catch (error) {
    console.error('H5环境下启动录音失败:', error);
    uni.showToast({
      title: '录音功能不可用',
      icon: 'none'
    });
    return;
  }
  // #endif
  
  // 非H5环境处理
  // #ifndef H5
  // 检查录音管理器是否可用
  if (!recorderManager) {
    try {
      initRecorder(); // 尝试重新初始化
      if (!recorderManager) {
        uni.showToast({
          title: '录音功能不可用',
          icon: 'none'
        });
        return;
      }
    } catch (error) {
      console.error('初始化录音管理器失败:', error);
      uni.showToast({
        title: '录音功能不可用',
        icon: 'none'
      });
      return;
    }
  }
  
  isRecording.value = true;
  recordDuration.value = 0;
  
  // 添加空值检查
  if (digitalHumans && digitalHumans.length > 0 && 
      currentDigitalHumanIndex.value >= 0 && 
      currentDigitalHumanIndex.value < digitalHumans.length) {
    const currentName = digitalHumans[currentDigitalHumanIndex.value].name;
    interactionText.value = `${currentName}正在聆听...`;
  } else {
    interactionText.value = '正在聆听...';
  }
  
  animateWaveform();
  
  // 重置触摸起始位置
  touchStartY.value = 0;
  
  // 实际开始录音
  recorderManager.start({
    duration: 60000, // 最长录音时间，单位ms，最大60s
    sampleRate: 16000, // 采样率
    numberOfChannels: 1, // 录音通道数
    encodeBitRate: 48000, // 编码码率
    format: 'mp3', // 音频格式
    frameSize: 50 // 指定帧大小
  });
  // #endif
};

// 修改呼叫数字人函数
const callDigitalHuman = () => {
  // 如果没有数字人数据，提示用户添加
  if (digitalHumans.length === 0) {
    showNoDigitalHumanTip()
    return
  }
  
  if (digitalHumans && digitalHumans.length > 0 && 
      currentDigitalHumanIndex.value >= 0 && 
      currentDigitalHumanIndex.value < digitalHumans.length) {
    
    const currentPhone = digitalHumans[currentDigitalHumanIndex.value].phone;
    
    if (currentPhone) {
      // 使用uni-app的API拨打电话
      uni.makePhoneCall({
        phoneNumber: currentPhone,
        success: () => {
          console.log('拨打电话成功');
        },
        fail: (err) => {
          console.error('拨打电话失败', err);
          // 在失败时显示提示
          uni.showToast({
            title: '拨打电话失败',
            icon: 'none'
          });
        }
      });
    } else {
      uni.showToast({
        title: '电话号码不可用',
        icon: 'none'
      });
    }
  } else {
    uni.showToast({
      title: '数字人信息不可用',
      icon: 'none'
    });
  }
}

// 帮助按钮点击
const onHelp = () => {
  uni.showModal({
    title: '帮助信息',
    content: '长按左侧麦克风按钮开始语音对话，松开发送语音消息，上滑取消录音。点击右侧电话按钮可以直接拨打当前数字人的联系电话。点击右侧的人物图标可以切换不同的数字人。点击右侧的齿轮图标可以进入数字人管理页面。点击右侧的调色板图标可以更换背景颜色。',
    showCancel: false
  })
}

// 设置按钮点击
const onSettings = () => {
  // 准备菜单选项
  let itemList = ['退出登录', '设置']
  
  // 检查数字人数据是否有效
  if (digitalHumans && digitalHumans.length > 0 && 
      currentDigitalHumanIndex.value >= 0 && 
      currentDigitalHumanIndex.value < digitalHumans.length) {
    // 如果有效，添加数字人详情选项
    itemList = ['退出登录', '数字人详情', '设置']
  }
  
  uni.showActionSheet({
    itemList: itemList,
    success: (res) => {
      if (res.tapIndex === 0) {
        // 退出登录
        uni.showModal({
          title: '提示',
          content: '确定要退出登录吗？',
          success: (res) => {
            if (res.confirm) {
              // 清除登录状态
              uni.removeStorageSync('isLoggedIn')
              uni.removeStorageSync('userInfo')
              
              // 跳转到登录页
              uni.reLaunch({
                url: '/pages/login/index'
              })
            }
          }
        })
      } else if (res.tapIndex === 1 && itemList.length > 2) {
        // 显示当前数字人详情（仅当有3个选项时）
        if (digitalHumans && digitalHumans.length > 0 && 
            currentDigitalHumanIndex.value >= 0 && 
            currentDigitalHumanIndex.value < digitalHumans.length) {
          uni.showModal({
            title: digitalHumans[currentDigitalHumanIndex.value].name,
            content: digitalHumans[currentDigitalHumanIndex.value].description,
            showCancel: false
          })
        }
      } else {
        // 设置（当只有2个选项时是索引1，有3个选项时是索引2）
        uni.showToast({
          title: '设置功能开发中',
          icon: 'none'
        })
      }
    }
  })
}

// 跳转到个人信息页面
const goToProfile = () => {
  uni.navigateTo({
    url: '/pages/profile/index'
  })
}

// 添加跳转到管理页面的方法
const goToManagePage = () => {
  uni.navigateTo({
    url: '/pages/manage/index',
    fail: (err) => {
      console.error('跳转到管理页面失败', err);
      uni.showToast({
        title: '页面跳转失败',
        icon: 'none'
      });
    }
  });
}

// 处理从API返回的数据，转换为前端使用的格式
const transformApiData = (apiData) => {
  console.log("转换API数据，完整原始数据:", apiData);
  
  // 确保图片路径拼接完整的URL
  const getFullUrl = (path) => {
    if (!path) return '/src/static/digital_human.jpg'; // 修改默认图片为digital_human.jpg
    
    // 如果路径已经是完整URL（以http开头），则直接返回
    if (path.startsWith('http://') || path.startsWith('https://')) {
      return path;
    }
    
    // 确保路径以/开头
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    // 不要在这里添加API前缀，因为服务返回的URL应该已经包含前缀
    return `${API_BASE_URL}${normalizedPath}`;
  };
  
  // 添加调试输出 - 检查各种可能的字段名称
  console.log("检查图片路径字段:");
  console.log("- image_path:", apiData.image_path);
  console.log("- avatar:", apiData.avatar);
  console.log("- imagePath:", apiData.imagePath);
  
  // 尝试获取图片路径，优先级：image_path > avatar > imagePath
  let imagePath = apiData.image_path || apiData.avatar || apiData.imagePath || null;
  console.log("最终使用的图片路径:", imagePath);
  
  const avatarUrl = getFullUrl(imagePath);
  console.log("处理后的完整图片URL:", avatarUrl);
  
  // 根据video_path判断训练状态
  const hasVideoPath = !!apiData.video_path;
  const isTrained = hasVideoPath;
  const trainingStatus = hasVideoPath ? 'trained' : 'untrained';
  
  console.log("训练状态判断:", {
    hasVideoPath,
    isTrained,
    trainingStatus
  });
  
  return {
    id: apiData.id,
    name: apiData.name,
    avatar: avatarUrl, // 确保avatar使用完整URL
    description: apiData.description,
    phone: apiData.phone,
    trainingAudio: getFullUrl(apiData.train_audio_path || apiData.trainingAudio), // 确保音频路径使用完整URL
    referenceAudio: getFullUrl(apiData.reference_audio_path || apiData.referenceAudio), // 确保音频路径使用完整URL
    video_path: apiData.video_path ? getFullUrl(apiData.video_path) : null, // 添加video_path字段
    trainingAudioLength: apiData.trainingAudioLength || '30秒',
    referenceAudioLength: apiData.referenceAudioLength || '5秒',
    user_id: apiData.user_id || 1, // 添加用户ID，默认为1
    is_trained: isTrained, // 根据video_path设置训练状态
    training_status: trainingStatus // 根据video_path设置训练状态
  };
}

// 修改数字人数据加载函数，使用API
const loadDigitalHumans = async () => {
  // 标记是否显示了加载提示
  let showedLoading = false
  
  try {
    // 设置加载状态
    loading.value = true
    
    // 显示加载提示，仅在首次加载时显示
    if (digitalHumans.length === 0) {
      uni.showLoading({
        title: '加载中...',
        mask: true
      })
      showedLoading = true
    }
    
    // 调用API获取数字人列表
    const response = await digitalHumanService.getDigitalHumans({
      skip: pagination.skip,
      limit: pagination.limit
    })
    
    if (response.success) {
      // 清空当前数组
      digitalHumans.splice(0, digitalHumans.length)
      
      // 使用Map来跟踪已添加的数字人，避免重复名称
      const namesMap = new Map();
      
      // 填充数据，转换API返回的字段名，并过滤重复名称
      response.data.items.forEach(item => {
        const transformedItem = transformApiData(item);
        // 检查是否已存在同名数字人
        if (!namesMap.has(transformedItem.name)) {
          digitalHumans.push(transformedItem);
          namesMap.set(transformedItem.name, true);
        }
      })
      
      // 更新总数
      pagination.total = response.data.total
      
      // 只有在API成功时才保存到本地存储
      uni.setStorageSync('digitalHumans', JSON.stringify(digitalHumans))
      
      // 有数字人时，设置交互文本
      if (digitalHumans.length > 0) {
        const currentName = digitalHumans[currentDigitalHumanIndex.value].name;
        interactionText.value = `和${currentName}聊天`;
      } else {
        interactionText.value = '请先添加家人';
      }
    } else {
      uni.showToast({
        title: response.message || '获取数字人失败',
        icon: 'none'
      })
      
      // API请求失败，尝试从本地存储加载
      loadFromStorage()
    }
  } catch (error) {
    console.error('加载数字人数据失败:', error)
    uni.showToast({
      title: '网络错误，使用本地数据',
      icon: 'none'
    })
    
    // 网络错误时，尝试从本地存储加载
    loadFromStorage()
  } finally {
    // 只有在显示了加载提示时才隐藏
    if (showedLoading) {
      uni.hideLoading()
    }
    
    // 重置加载状态
    loading.value = false
  }
}

// 从本地存储加载数据
const loadFromStorage = () => {
  try {
    // 清空当前数组
    digitalHumans.splice(0, digitalHumans.length)
    
    const savedData = uni.getStorageSync('digitalHumans')
    if (savedData) {
      const parsedData = JSON.parse(savedData)
      if (Array.isArray(parsedData) && parsedData.length > 0) {
        // 使用Map来跟踪已添加的数字人，避免重复名称
        const namesMap = new Map();
        
        // 添加存储的数据，过滤重复名称
        parsedData.forEach(item => {
          // 检查是否已存在同名数字人
          if (!namesMap.has(item.name)) {
            digitalHumans.push(item);
            namesMap.set(item.name, true);
          }
        })
        
        // 如果过滤后还有数字人，更新本地存储
        if (digitalHumans.length !== parsedData.length) {
          uni.setStorageSync('digitalHumans', JSON.stringify(digitalHumans));
        }
        
        // 有数字人时，设置交互文本
        if (digitalHumans.length > 0) {
          const currentName = digitalHumans[currentDigitalHumanIndex.value].name;
          interactionText.value = `和${currentName}聊天`;
        } else {
          interactionText.value = '请先添加家人'
          currentDigitalHumanIndex.value = 0
        }
        
        // 尝试恢复之前选择的数字人
        try {
          const savedId = uni.getStorageSync('currentDigitalHumanId')
          if (savedId) {
            const found = digitalHumans.findIndex(item => item.id === savedId)
            if (found >= 0) {
              currentDigitalHumanIndex.value = found
            } else {
              currentDigitalHumanIndex.value = 0
            }
          } else {
            currentDigitalHumanIndex.value = 0
          }
        } catch (e) {
          currentDigitalHumanIndex.value = 0
        }
      } else {
        // 无数字人时，设置提示文本
        interactionText.value = '请先添加家人'
        currentDigitalHumanIndex.value = 0
      }
    } else {
      // 没有存储数据时，设置提示文本
      interactionText.value = '请先添加家人'
      currentDigitalHumanIndex.value = 0
    }
  } catch (e) {
    console.error('从本地存储加载数据失败:', e)
    // 清空数组
    digitalHumans.splice(0, digitalHumans.length)
    // 设置提示文本
    interactionText.value = '请先添加家人'
    // 重置索引
    currentDigitalHumanIndex.value = 0
  }
}

// 添加无数字人提示函数
const showNoDigitalHumanTip = () => {
  uni.showModal({
    title: '无可用家人',
    content: '您还没有添加任何家人，请先前往家人管理页面添加',
    confirmText: '去添加',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        goToManagePage()
      }
    }
  })
}

// 添加未训练提示函数
const showNotTrainedTip = () => {
  uni.showModal({
    title: '家人未训练',
    content: '当前家人尚未完成训练，无法进行语音对话。请先在管理页面完成训练。',
    confirmText: '去训练',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        goToManagePage()
      }
    }
  })
}

// 添加页面重载函数
const reloadPage = async () => {
  // 显示加载提示
  uni.showLoading({
    title: '刷新中...',
    mask: true
  })
  
  try {
    // 重置分页参数
    pagination.skip = 0
    
    // 重新加载数据
    await loadDigitalHumans()
    
    // 显示成功提示
    uni.showToast({
      title: '数据已刷新',
      icon: 'success'
    })
  } catch (error) {
    // 错误提示
    uni.showToast({
      title: '刷新失败',
      icon: 'none'
    })
  } finally {
    // 隐藏加载提示
    uni.hideLoading()
  }
}

// 使用uni-app的页面生命周期
// 注意：uni-app的页面生命周期钩子不是从Vue导入的，而是在setup中定义的函数
// 组件挂载时加载数据
onMounted(() => {
  // 只在挂载时加载数据一次
  loadDigitalHumans()
  
  // 延迟初始化录音管理器，确保页面已完全加载
  setTimeout(() => {
    initRecorder();
  }, 500);
  
  // 恢复用户选择的背景颜色
  const savedColor = uni.getStorageSync('bgColor');
  if (savedColor && bgColors.includes(savedColor)) {
    currentBgColor.value = savedColor;
  }
  
  // 设置页面标题
  uni.setNavigationBarTitle({
    title: '家人聊天'
  })
})

// 修改页面显示生命周期函数
const onShow = () => {
  // 设置页面标题
  uni.setNavigationBarTitle({
    title: '家人聊天'
  })
}

// 定义获取当前页面栈的函数
const getCurrentPages = () => {
  // 调用uni-app的getCurrentPages API
  try {
    return uni.getCurrentPages()
  } catch (e) {
    console.error('获取页面栈失败:', e)
    return []
  }
}

// 声明页面生命周期钩子
defineExpose({
  onShow
});

// 增加一个专门的点击处理函数，代替三元表达式
const handleDigitalHumanToggle = () => {
  if (digitalHumans.length > 0) {
    // 有数字人时正常切换展开/收起状态
    isDigitalHumanExpanded.value = !isDigitalHumanExpanded.value
    
    // 如果展开数字人选择器，则收起主题选择器
    if (isDigitalHumanExpanded.value && isThemeExpanded.value) {
      isThemeExpanded.value = false
    }
  } else {
    // 没有数字人时显示提示
    showNoDigitalHumanTip()
  }
}

// 添加关闭数字人选择弹窗的函数
const closeDigitalHumanPopup = () => {
  // 直接关闭弹窗
  isDigitalHumanExpanded.value = false
}

// 组件卸载时清理资源
onUnmounted(() => {
  stopWaveformAnimation();
  
  // 清理录音相关资源
  if (recordTimer) {
    clearInterval(recordTimer);
  }
})

// 播放生成的语音
const playAudio = async (audioUrl) => {
  try {
    // 创建内部音频上下文
    const innerAudioContext = uni.createInnerAudioContext();
    
    // 设置音频源
    innerAudioContext.src = audioUrl;
    
    // 基本配置
    innerAudioContext.volume = 1.0;
    innerAudioContext.playbackRate = 1.0;
    
    // 设置为播放状态，显示GIF
    isPlayingAudio.value = true;
    
    // 监听音频加载完成事件
    innerAudioContext.onCanplay(() => {
      console.log('音频加载完成，开始播放');
      // 直接开始播放
      innerAudioContext.play();
    });
    
    // 监听音频播放进度
    innerAudioContext.onTimeUpdate(() => {
      console.log('当前播放时间:', innerAudioContext.currentTime, '总时长:', innerAudioContext.duration);
    });
    
    // 监听播放结束
    innerAudioContext.onEnded(() => {
      console.log('音频播放结束');
      innerAudioContext.destroy();
      interactionText.value = '语音播放完成';
      
      // 播放结束，恢复显示图片
      isPlayingAudio.value = false;
      
      // 3秒后恢复默认提示
      setTimeout(() => {
        interactionText.value = '按住按钮开始语音对话';
      }, 3000);
    });
    
    // 监听错误
    innerAudioContext.onError((err) => {
      console.error('播放语音错误:', err);
      innerAudioContext.destroy();
      uni.showToast({
        title: '播放语音失败',
        icon: 'none'
      });
      interactionText.value = '按住按钮开始语音对话';
      
      // 错误时也恢复显示图片
      isPlayingAudio.value = false;
    });
    
    // 开始加载并自动播放
    innerAudioContext.autoplay = true;
  } catch (error) {
    console.error('创建音频上下文失败:', error);
    uni.showToast({
      title: '音频播放失败',
      icon: 'none'
    });
    isPlayingAudio.value = false;
  }
};
</script>

<style>
.home-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  transition: background-color 0.3s ease;
}

/* 顶部导航栏样式 */
.header {
  height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30rpx;
  background-color: #fff;
  border-bottom: 1rpx solid #ecf0f1;
  position: relative;
  z-index: 10;
}

.header-left {
  display: flex;
  align-items: center;
  width: 60rpx;
  flex-shrink: 0;
}

.header-center {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.header-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
  text-align: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.icon-wrapper {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-logo {
  width: 60rpx;
  height: 60rpx;
  background-color: #3498db;
  border-radius: 12rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-image {
  width: 40rpx;
  height: 40rpx;
}

/* 中央内容区样式 */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30rpx;
  position: relative;
}

.avatar-area {
  width: 100%;
  height: 700rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
  position: relative;
}

.avatar-placeholder {
  width: 650rpx;
  height: 650rpx;
  background-color: rgba(236, 240, 241, 0.5);
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  position: relative;
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.1);
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.digital-human-name {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.6), transparent);
  padding: 20rpx 0;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.digital-human-name text {
  color: #fff;
  font-size: 32rpx;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  margin-bottom: 10rpx;
}

.training-badge {
  font-size: 22rpx;
  padding: 6rpx 16rpx;
  border-radius: 20rpx;
  color: #fff;
  margin-top: 6rpx;
}

.training-badge.untrained {
  background-color: #e74c3c;
}

.training-badge.training {
  background-color: #f39c12;
}

.training-badge.trained {
  background-color: #2ecc71;
}

.placeholder-text {
  font-size: 28rpx;
  color: #95a5a6;
  text-align: center;
  padding: 40rpx;
}

/* 功能按钮区域 */
.function-buttons {
  width: 100%;
  padding: 20rpx 30rpx;
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 30rpx;
}

.button-row {
  display: flex;
  justify-content: space-between;
  gap: 30rpx;
}

.function-button {
  flex: 1;
  height: 180rpx;
  background-color: #fff;
  border-radius: 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.function-button:active {
  transform: scale(0.98);
  background-color: #f8f8f8;
}

.function-button .button-label {
  font-size: 28rpx;
  color: #666;
  margin-top: 16rpx;
}

.digital-human-toggle.expanded {
  background-color: #3498db;
}

.digital-human-toggle.expanded uni-icons {
  color: #fff;
}

.digital-human-toggle.expanded .button-label {
  color: #fff;
}

.theme-toggle.expanded {
  transform: rotate(45deg);
}

.function-button.disabled {
  background-color: #f2f2f2;
  box-shadow: none;
  opacity: 0.6;
  cursor: not-allowed;
}

.function-button.disabled .button-label {
  color: #999;
}

/* 数字人选择浮层 */
.digital-human-popup {
  position: fixed;
  left: 50rpx;
  right: 50rpx;
  bottom: 200rpx;
  background-color: #fff;
  border-radius: 20rpx;
  box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.15);
  z-index: 101;
  padding: 30rpx;
  max-height: 800rpx;
  overflow-y: auto;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.popup-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.popup-close {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 30rpx;
}

.digital-human-grid {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.digital-human-card {
  display: flex;
  align-items: center;
  padding: 20rpx;
  border-radius: 15rpx;
  background-color: #f8f8f8;
  transition: all 0.2s ease;
}

.digital-human-card.active {
  background-color: rgba(52, 152, 219, 0.1);
  border-left: 6rpx solid #3498db;
}

.digital-human-portrait {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  border: 3rpx solid #fff;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
  object-fit: cover;
  margin-right: 20rpx;
}

.digital-human-info {
  flex: 1;
}

.digital-human-name-text {
  font-size: 30rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 10rpx;
  display: block;
}

.digital-human-desc {
  font-size: 24rpx;
  color: #666;
  display: block;
  margin-bottom: 10rpx;
}

.card-badge {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  color: #fff;
  display: inline-block;
}

.card-badge.untrained {
  background-color: #e74c3c;
}

.card-badge.training {
  background-color: #f39c12;
}

.card-badge.trained {
  background-color: #2ecc71;
}

.digital-human-card.active .digital-human-name-text {
  color: #3498db;
}

/* 主题切换器样式 */
.theme-colors {
  position: fixed;
  right: 170rpx;
  bottom: 280rpx;
  z-index: 100;
  display: flex;
  flex-direction: column;
  gap: 15rpx;
  background-color: #fff;
  padding: 20rpx;
  border-radius: 15rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.1);
}

.color-option {
  width: 60rpx;
  height: 60rpx;
  border-radius: 30rpx;
  border: 2rpx solid #fff;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.color-option.active {
  transform: scale(1.1);
  border: 2rpx solid #3498db;
}

.interaction-area {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 40rpx 0;
  padding: 0 30rpx;
}

.interaction-text {
  font-size: 40rpx;
  color: #333;
  margin-bottom: 30rpx;
  text-align: center;
  font-weight: 600;
  text-shadow: 0 2rpx 4rpx rgba(0, 0, 0, 0.1);
  padding: 20rpx 40rpx;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 30rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.waveform {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 120rpx;
  width: 500rpx;
}

.wave-bar {
  width: 12rpx;
  background-color: #3498db;
  margin: 0 6rpx;
  border-radius: 6rpx;
  transition: height 0.1s ease;
}

/* 底部操作栏样式 */
.footer {
  height: 160rpx;
  background-color: #fff;
  border-top: 1rpx solid #ecf0f1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 30rpx;
}

.footer-buttons {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40rpx;
}

.voice-button-container {
  position: relative;
}

.voice-button {
  width: 120rpx;
  height: 120rpx;
  background-color: #3498db;
  border-radius: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 15rpx rgba(52, 152, 219, 0.3);
  transition: all 0.2s ease;
}

.voice-button.recording {
  background-color: #e74c3c;
  transform: scale(1.1);
}

.call-button-container {
  position: relative;
}

.call-button {
  width: 120rpx;
  height: 120rpx;
  background-color: #27ae60;
  border-radius: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6rpx 15rpx rgba(39, 174, 96, 0.3);
  transition: all 0.2s ease;
}

.call-button:active {
  transform: scale(0.95);
  background-color: #219653;
}

.cancel-area {
  position: absolute;
  top: -80rpx;
  left: 50%;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.6);
  color: #fff;
  padding: 10rpx 20rpx;
  border-radius: 10rpx;
  font-size: 24rpx;
}

/* 空状态样式 */
.empty-digital-human {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background-color: rgba(236, 240, 241, 0.5);
  border-radius: 30rpx;
}

.empty-image {
  width: 200rpx;
  height: 200rpx;
  margin-bottom: 30rpx;
  opacity: 0.7;
}

.empty-image-small {
  width: 120rpx;
  height: 120rpx;
  margin-bottom: 20rpx;
  opacity: 0.7;
}

.empty-text {
  font-size: 28rpx;
  color: #95a5a6;
  text-align: center;
  margin-bottom: 30rpx;
}

.add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #3498db;
  color: #fff;
  padding: 20rpx 40rpx;
  border-radius: 45rpx;
  font-size: 28rpx;
  box-shadow: 0 4rpx 12rpx rgba(52, 152, 219, 0.3);
}

.add-btn-small {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #3498db;
  color: #fff;
  padding: 12rpx 30rpx;
  border-radius: 30rpx;
  font-size: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(52, 152, 219, 0.3);
}

.add-btn text, .add-btn-small text {
  margin-left: 8rpx;
  color: #fff;
}

.empty-popup-state {
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.call-button.disabled {
  background-color: #b3b3b3;
  box-shadow: none;
  opacity: 0.6;
  pointer-events: none; /* 完全禁用点击 */
}

.function-button.disabled {
  background-color: #f2f2f2;
  box-shadow: none;
  opacity: 0.6;
  cursor: not-allowed;
}

.function-button.disabled .button-label {
  color: #999;
}
</style>
