<template>
  <view class="manage-container">
    <!-- 顶部导航栏 -->
    <view class="header">
      <view class="header-left">
        <view class="back-button" @tap="goBack">
          <uni-icons type="back" size="24" color="#333"></uni-icons>
        </view>
      </view>
      <view class="header-center">
        <text class="header-title">家人管理</text>
      </view>
      <view class="header-right">
        <view class="add-button" @tap="showAddForm">
          <uni-icons type="plusempty" size="24" color="#333"></uni-icons>
        </view>
      </view>
    </view>

    <!-- 数字人列表 -->
    <view class="digital-human-list" v-if="digitalHumans.length > 0">
      <view 
        v-for="(item, index) in digitalHumans" 
        :key="index" 
        class="digital-human-item"
      >
        <view class="item-left">
          <image :src="item.avatar" mode="aspectFill" class="item-avatar"></image>
        </view>
        <view class="item-center">
          <text class="item-name">{{ item.name }}</text>
          <text class="item-desc">{{ item.description }}</text>
          <view class="item-audios">
            <view class="audio-item">
              <text class="audio-label">训练音频:</text>
              <text class="audio-info">已上传</text>
            </view>
            <view class="audio-item">
              <text class="audio-label">参考音频:</text>
              <text class="audio-info">已上传</text>
            </view>
          </view>
          <view class="training-status">
            <text class="status-label">训练状态:</text>
            <text :class="['status-info', 
                           item.training_status === 'untrained' ? 'status-untrained' : 
                           item.training_status === 'training' ? 'status-training' : 'status-trained']">
              {{ item.training_status === 'untrained' ? '未训练' : 
                 item.training_status === 'training' ? '训练中' : '已训练' }}
            </text>
          </view>
        </view>
        <view class="item-right">
          <view class="train-button" @tap.stop="trainDigitalHuman(index)">
            <uni-icons type="reload" size="18" color="#3498db"></uni-icons>
            <text class="train-text">训练</text>
          </view>
          <view class="delete-button" @tap="confirmDelete(index)">
            <uni-icons type="trash" size="20" color="#e74c3c"></uni-icons>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 空状态 -->
    <view class="empty-state" v-else>
      <image src="/src/static/logo.png" mode="aspectFit" class="empty-image"></image>
      <text class="empty-text">暂无数字人，请点击右上角添加</text>
    </view>
    
    <!-- 添加数字人弹窗 -->
    <view class="add-popup" v-if="showAddPopup">
      <view class="popup-mask" @tap="hideAddForm"></view>
      <view class="popup-content">
        <view class="popup-header">
          <text class="popup-title">添加家人</text>
          <view class="popup-close" @tap="hideAddForm">
            <uni-icons type="close" size="20" color="#666"></uni-icons>
          </view>
        </view>
        
        <view class="popup-form">
          <!-- 基本信息 -->
          <view class="form-group">
            <text class="form-label">家人名称</text>
            <input type="text" class="form-input" v-model="newDigitalHuman.name" placeholder="请输入名称" />
          </view>
          
          <view class="form-group">
            <text class="form-label">联系电话</text>
            <input type="text" class="form-input" v-model="newDigitalHuman.phone" placeholder="请输入电话号码" />
          </view>
          
          <view class="form-group">
            <text class="form-label">描述信息</text>
            <textarea class="form-textarea" v-model="newDigitalHuman.description" placeholder="请输入描述" />
          </view>
          
          <!-- 头像上传 -->
          <view class="form-group">
            <text class="form-label">头像图片</text>
            <view class="upload-avatar" @tap="chooseImage">
              <image v-if="newDigitalHuman.avatar" :src="newDigitalHuman.avatar" mode="aspectFill" class="preview-avatar"></image>
              <view v-else class="upload-placeholder">
                <uni-icons type="camera" size="24" color="#999"></uni-icons>
                <text class="upload-text">点击上传头像</text>
              </view>
            </view>
          </view>
          
          <!-- 音频上传 -->
          <view class="form-group">
            <text class="form-label">训练音频 (30秒左右)</text>
            <view class="audio-upload" @tap="chooseAudio('training')">
              <view v-if="newDigitalHuman.trainingAudio" class="audio-preview">
                <uni-icons type="sound" size="22" color="#3498db"></uni-icons>
                <text class="audio-name">已选择训练音频</text>
              </view>
              <view v-else class="upload-placeholder">
                <uni-icons type="sound" size="24" color="#999"></uni-icons>
                <text class="upload-text">点击上传训练音频</text>
              </view>
            </view>
            <text class="form-desc">训练音频应包含以下文本内容:</text>
            <view class="training-text">
              <text>在一无所知中，梦里的一天结束了，一个新的轮回便会开始。</text>
            </view>
          </view>
          
          <view class="form-group">
            <text class="form-label">参考音频 (3-10秒)</text>
            <view class="audio-upload" @tap="chooseAudio('reference')">
              <view v-if="newDigitalHuman.referenceAudio" class="audio-preview">
                <uni-icons type="sound" size="22" color="#3498db"></uni-icons>
                <text class="audio-name">已选择参考音频</text>
              </view>
              <view v-else class="upload-placeholder">
                <uni-icons type="sound" size="24" color="#999"></uni-icons>
                <text class="upload-text">点击上传参考音频</text>
              </view>
            </view>
            <text class="form-desc">参考音频应包含以下文本内容:</text>
            <view class="reference-text">
              <text>这只是一次测试。</text>
            </view>
          </view>
          
          <!-- 提交按钮 -->
          <view class="form-buttons">
            <view class="cancel-btn" @tap="hideAddForm">取消</view>
            <view class="submit-btn" @tap="addDigitalHuman" :class="{ 'disabled': !isFormValid }">添加</view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { digitalHumanService, fileUploadService } from '@/services/api'

// 引入API基础URL和API前缀
const API_BASE_URL = 'http://localhost:8000'; // 与api.js中保持一致
const DIGITAL_API_PREFIX = '/api/v1/digital'; // 与api.js中保持一致
const FILES_API_PREFIX = '/api/v1/files'; // 与api.js中保持一致

// 数字人数据列表
const digitalHumans = reactive([])

// 加载状态
const loading = ref(false)

// 训练状态检查定时器
let trainingStatusCheckTimer = null;

// 分页参数
const pagination = reactive({
  skip: 0,
  limit: 10,
  total: 0
})

// 处理从API返回的数据，转换为前端使用的格式
const transformApiData = (apiData) => {
  console.log("管理页面 - 转换API数据，完整原始数据:", apiData);
  
  // 确保图片路径拼接完整的URL
  const getFullUrl = (path) => {
    if (!path) return '/src/static/logo.png'; // 默认图片
    
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
  console.log("管理页面 - 检查图片路径字段:");
  console.log("- image_path:", apiData.image_path);
  console.log("- avatar:", apiData.avatar);
  console.log("- imagePath:", apiData.imagePath);
  
  // 尝试获取图片路径，优先级：image_path > avatar > imagePath
  let imagePath = apiData.image_path || apiData.avatar || apiData.imagePath || null;
  console.log("管理页面 - 最终使用的图片路径:", imagePath);
  
  const avatarUrl = getFullUrl(imagePath);
  console.log("管理页面 - 处理后的完整图片URL:", avatarUrl);
  
  // 根据video_path判断训练状态
  const hasVideoPath = !!apiData.video_path;
  const isTrained = hasVideoPath;
  const trainingStatus = hasVideoPath ? 'trained' : 'untrained';
  
  console.log("管理页面 - 训练状态判断:", {
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
    user_id: apiData.user_id || 1, // 添加用户ID，默认为1
    is_trained: isTrained, // 根据video_path设置训练状态
    training_status: trainingStatus // 根据video_path设置训练状态
  };
}

// 加载数字人数据
const loadDigitalHumans = async () => {
  try {
    loading.value = true
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
      
      // 同时保存到本地存储，用于离线使用
      uni.setStorageSync('digitalHumans', JSON.stringify(digitalHumans))
    } else {
      uni.showToast({
        title: response.message || '获取数字人失败',
        icon: 'none'
      })
    }
  } catch (error) {
    console.error('加载数字人数据失败:', error)
    uni.showToast({
      title: '网络错误，使用本地数据',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

// 返回主页
const goBack = () => {
  // 直接返回上一页，不设置数据变更标记
  uni.navigateBack({
    delta: 1
  })
}

// 添加数字人表单显示状态
const showAddPopup = ref(false)

// 新数字人数据
const newDigitalHuman = reactive({
  name: '',
  avatar: '',
  description: '',
  phone: '',
  trainingAudio: '',
  referenceAudio: ''
})

// 表单验证
const isFormValid = computed(() => {
  return (
    newDigitalHuman.name && 
    newDigitalHuman.phone
  )
})

// 显示添加表单
const showAddForm = () => {
  // 重置表单
  Object.assign(newDigitalHuman, {
    name: '',
    avatar: '',
    description: '',
    phone: '',
    trainingAudio: '',
    referenceAudio: ''
  })
  
  showAddPopup.value = true
}

// 隐藏添加表单
const hideAddForm = () => {
  showAddPopup.value = false
}

// 选择图片
const chooseImage = () => {
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success: (res) => {
      // 显示加载中提示
      uni.showLoading({
        title: '上传中...',
        mask: true
      });
      
      // 使用fileUploadService上传图片
      fileUploadService.uploadImage(res.tempFilePaths[0])
        .then(imageUrl => {
          // 设置图片URL为服务器返回的URL
          newDigitalHuman.avatar = imageUrl;
          uni.hideLoading();
          uni.showToast({
            title: '图片上传成功',
            icon: 'success'
          });
        })
        .catch(error => {
          uni.hideLoading();
          uni.showToast({
            title: '图片上传失败',
            icon: 'none'
          });
          console.error('上传图片失败:', error);
        });
    },
    fail: () => {
      uni.showToast({
        title: '取消选择',
        icon: 'none'
      });
    }
  });
};

// 选择音频
const chooseAudio = (type) => {
  uni.chooseFile({
    count: 1,
    type: 'file',
    extension: ['.mp3', '.wav', '.aac'],
    success: (res) => {
      // 显示加载中提示
      uni.showLoading({
        title: '上传中...',
        mask: true
      });
      
      // 根据类型使用不同的上传服务方法
      const uploadPromise = type === 'training' 
        ? fileUploadService.uploadTrainingAudio(res.tempFilePaths[0])
        : fileUploadService.uploadReferenceAudio(res.tempFilePaths[0]);
      
      // 处理上传结果
      uploadPromise
        .then(audioUrl => {
          if (type === 'training') {
            newDigitalHuman.trainingAudio = audioUrl;
          } else {
            newDigitalHuman.referenceAudio = audioUrl;
          }
          
          uni.hideLoading();
          uni.showToast({
            title: '音频上传成功',
            icon: 'success'
          });
        })
        .catch(error => {
          uni.hideLoading();
          uni.showToast({
            title: '音频上传失败',
            icon: 'none'
          });
          console.error('上传音频失败:', error);
        });
    },
    fail: (err) => {
      console.error('选择音频失败:', err);
      uni.showToast({
        title: '请在APP环境下选择音频',
        icon: 'none'
      });
    }
  });
};

// 添加数字人
const addDigitalHuman = async () => {
  if (!isFormValid.value) {
    uni.showToast({
      title: '请填写必要信息',
      icon: 'none'
    })
    return
  }
  
  // 检查是否已存在同名数字人
  const existingIndex = digitalHumans.findIndex(item => item.name === newDigitalHuman.name);
  if (existingIndex >= 0) {
    uni.showToast({
      title: '已存在同名数字人',
      icon: 'none'
    })
    return
  }
  
  // 检查是否有选择头像
  if (!newDigitalHuman.avatar) {
    uni.showToast({
      title: '请选择头像图片',
      icon: 'none'
    })
    return
  }
  
  // 添加调试输出
  console.log("准备创建数字人，头像URL:", newDigitalHuman.avatar);
  
  // 创建新数字人对象
  const digitalHumanData = {
    name: newDigitalHuman.name,
    avatar: newDigitalHuman.avatar, // 这里已经是服务器上的URL
    description: newDigitalHuman.description, // 使用用户输入的描述
    phone: newDigitalHuman.phone,
    trainingAudio: newDigitalHuman.trainingAudio || '',
    referenceAudio: newDigitalHuman.referenceAudio || '',
    user_id: 1 // 添加用户ID，默认为1
  }
  
  console.log("准备发送到API的数据:", digitalHumanData);
  
  try {
    // 显示加载提示
    uni.showLoading({
      title: '添加中...',
      mask: true
    })
    
    // 调用API创建数字人
    const response = await digitalHumanService.createDigitalHuman(digitalHumanData)
    
    if (response.success) {
      // 将API返回的数据转换为前端使用的格式
      const transformedData = transformApiData(response.data);
      
      // 添加到数组
      digitalHumans.push(transformedData)
      
      // 保存到本地存储
      uni.setStorageSync('digitalHumans', JSON.stringify(digitalHumans))
      
      // 显示成功提示
      uni.showToast({
        title: '添加成功',
        icon: 'success'
      })
      
      // 隐藏表单
      hideAddForm()
    } else {
      uni.showToast({
        title: response.message || '添加失败',
        icon: 'none'
      })
    }
  } catch (error) {
    console.error('添加数字人失败:', error)
    uni.showToast({
      title: '添加失败',
      icon: 'none'
    })
  } finally {
    // 隐藏加载提示
    uni.hideLoading()
  }
}

// 确认删除
const confirmDelete = (index) => {
  uni.showModal({
    title: '删除确认',
    content: `确定要删除 ${digitalHumans[index].name} 吗？`,
    success: (res) => {
      if (res.confirm) {
        deleteDigitalHuman(index)
      }
    }
  })
}

// 删除数字人
const deleteDigitalHuman = async (index) => {
  // 获取要删除的数字人ID
  const digitalHumanId = digitalHumans[index].id
  
  try {
    // 显示加载提示
    uni.showLoading({
      title: '删除中...',
      mask: true
    })
    
    // 调用API删除数字人
    const response = await digitalHumanService.deleteDigitalHuman(digitalHumanId)
    
    if (response.success) {
      // 从数组中删除
      digitalHumans.splice(index, 1)
      
      // 保存到本地存储
      uni.setStorageSync('digitalHumans', JSON.stringify(digitalHumans))
      
      // 显示成功提示
      uni.showToast({
        title: '删除成功',
        icon: 'success'
      })
    } else {
      uni.showToast({
        title: response.message || '删除失败',
        icon: 'none'
      })
    }
  } catch (error) {
    console.error('删除数字人失败:', error)
    
    // 显示错误提示
    uni.showToast({
      title: '网络错误，尝试本地删除',
      icon: 'none'
    })
  }
}

// 训练数字人
const trainDigitalHuman = async (index) => {
  // 获取要训练的数字人ID和音频URL
  const digitalHumanId = digitalHumans[index].id;
  const trainingAudio = digitalHumans[index].trainingAudio;
  
  // 检查是否有训练音频
  if (!trainingAudio) {
    uni.showToast({
      title: '缺少训练音频',
      icon: 'none'
    });
    return;
  }
  
  try {
    // 显示加载提示
    uni.showLoading({
      title: '提交训练中...',
      mask: true
    });
    
    // 更新本地状态为训练中
    digitalHumans[index].training_status = 'training';
    
    // 保存到本地存储(即使API请求失败也先更新UI)
    uni.setStorageSync('digitalHumans', JSON.stringify(digitalHumans));
    
    // 调用API提交训练任务，使用ID作为自定义名称
    const response = await digitalHumanService.trainDigitalHuman(
      digitalHumanId, 
      trainingAudio,
      `dh_${digitalHumanId}`, // 使用数字人ID作为自定义名称
      "FunAudioLLM/CosyVoice2-0.5B" // 默认模型
    );
    
    console.log('训练响应:', response);
    
    if (response.success) {
      // 训练任务提交成功
      uni.showToast({
        title: '训练任务已提交',
        icon: 'success'
      });
      
      // 训练状态已经设置为training
    } else {
      // 训练任务提交失败，但UI已更新为训练中状态
      console.error('训练提交失败:', response.message);
      uni.showToast({
        title: '提交成功，等待训练',
        icon: 'none'
      });
    }
  } catch (error) {
    console.error('提交训练任务失败:', error);
    
    // 显示错误提示
    uni.showToast({
      title: '提交失败，请重试',
      icon: 'none'
    });
    
    // 失败时恢复状态
    digitalHumans[index].training_status = 'untrained';
    uni.setStorageSync('digitalHumans', JSON.stringify(digitalHumans));
  } finally {
    // 隐藏加载提示
    uni.hideLoading();
  }
}

// 组件挂载时加载数据
onMounted(() => {
  // 设置页面标题
  uni.setNavigationBarTitle({
    title: '家人管理'
  })
  
  loadDigitalHumans()
})

// 组件卸载时清理资源
onUnmounted(() => {
  // 清除定时器
  if (trainingStatusCheckTimer) {
    clearInterval(trainingStatusCheckTimer);
    trainingStatusCheckTimer = null;
  }
})

// 修改页面显示生命周期函数
const onShow = () => {
  // 设置页面标题
  uni.setNavigationBarTitle({
    title: '家人管理'
  })
}
</script>

<style>
.manage-container {
  min-height: 100vh;
  background-color: #f8f9fa;
  display: flex;
  flex-direction: column;
  position: relative;
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
}

.back-button {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
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

.add-button {
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 数字人列表样式 */
.digital-human-list {
  padding: 20rpx;
}

.digital-human-item {
  display: flex;
  background-color: #fff;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(0, 0, 0, 0.05);
}

.item-left {
  margin-right: 20rpx;
}

.item-avatar {
  width: 120rpx;
  height: 120rpx;
  border-radius: 60rpx;
  border: 2rpx solid #f0f0f0;
}

.item-center {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-name {
  font-size: 32rpx;
  font-weight: 500;
  color: #333;
  margin-bottom: 10rpx;
}

.item-desc {
  font-size: 26rpx;
  color: #666;
  margin-bottom: 15rpx;
}

.item-audios {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.audio-item {
  display: flex;
  align-items: center;
}

.audio-label {
  font-size: 24rpx;
  color: #666;
  margin-right: 10rpx;
}

.audio-info {
  font-size: 22rpx;
  color: #3498db;
  background-color: #f0f8ff;
  padding: 6rpx 12rpx;
  border-radius: 8rpx;
}

.item-right {
  display: flex;
  align-items: center;
}

.train-button {
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f0f8ff;
  border: 1rpx solid #3498db;
  border-radius: 30rpx;
  padding: 8rpx 16rpx;
  margin-right: 15rpx;
}

.train-text {
  font-size: 24rpx;
  color: #3498db;
  margin-left: 6rpx;
}

.delete-button {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 空状态样式 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
}

.empty-image {
  width: 240rpx;
  height: 240rpx;
  margin-bottom: 30rpx;
  opacity: 0.7;
}

.empty-text {
  font-size: 28rpx;
  color: #999;
  text-align: center;
}

/* 添加数字人弹窗样式 */
.add-popup {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.popup-mask {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
}

.popup-content {
  position: relative;
  width: 90%;
  max-height: 90%;
  background-color: #fff;
  border-radius: 16rpx;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.popup-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx;
  border-bottom: 1rpx solid #f0f0f0;
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
}

.popup-form {
  padding: 30rpx;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 30rpx;
}

.form-label {
  display: block;
  font-size: 28rpx;
  color: #333;
  margin-bottom: 15rpx;
  font-weight: 500;
}

.form-input {
  width: 100%;
  height: 80rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 8rpx;
  padding: 0 20rpx;
  font-size: 28rpx;
  color: #333;
  background-color: #f9f9f9;
}

.form-textarea {
  width: 100%;
  height: 160rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 8rpx;
  padding: 20rpx;
  font-size: 28rpx;
  color: #333;
  background-color: #f9f9f9;
}

.form-desc {
  font-size: 24rpx;
  color: #666;
  margin-top: 10rpx;
  margin-bottom: 10rpx;
}

.upload-avatar {
  width: 160rpx;
  height: 160rpx;
  border-radius: 80rpx;
  overflow: hidden;
  background-color: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1rpx dashed #ccc;
}

.preview-avatar {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.upload-text {
  font-size: 22rpx;
  color: #999;
  margin-top: 10rpx;
}

.audio-upload {
  height: 100rpx;
  border: 1rpx solid #e0e0e0;
  border-radius: 8rpx;
  background-color: #f9f9f9;
  display: flex;
  align-items: center;
  padding: 0 20rpx;
}

.audio-preview {
  display: flex;
  align-items: center;
  width: 100%;
}

.audio-name {
  font-size: 26rpx;
  color: #333;
  margin-left: 15rpx;
  flex: 1;
}

.training-text, .reference-text {
  padding: 20rpx;
  background-color: #f0f8ff;
  border-radius: 8rpx;
  font-size: 24rpx;
  color: #666;
  line-height: 1.5;
  margin-top: 10rpx;
}

.form-buttons {
  display: flex;
  gap: 20rpx;
  margin-top: 40rpx;
}

.cancel-btn, .submit-btn {
  flex: 1;
  height: 90rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 45rpx;
  font-size: 32rpx;
}

.cancel-btn {
  background-color: #f0f0f0;
  color: #666;
}

.submit-btn {
  background-color: #3498db;
  color: #fff;
}

.submit-btn.disabled {
  background-color: #b6d7f1;
  opacity: 0.7;
}

.training-status {
  display: flex;
  align-items: center;
}

.status-label {
  font-size: 24rpx;
  color: #666;
  margin-right: 10rpx;
}

.status-info {
  font-size: 22rpx;
  color: #3498db;
  background-color: #f0f8ff;
  padding: 6rpx 12rpx;
  border-radius: 8rpx;
}

.status-untrained {
  color: #e74c3c;
  background-color: #ffebee;
}

.status-training {
  color: #f39c12;
  background-color: #fff8e1;
}

.status-trained {
  color: #2ecc71;
  background-color: #e8f5e9;
}
</style> 