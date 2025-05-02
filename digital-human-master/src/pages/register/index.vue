<template>
  <view class="register-container">
    <!-- Logo区域 -->
    <view class="logo-section">
      <view class="logo-container">
        <image src="/src/static/logo.png" mode="aspectFit" class="logo"></image>
      </view>
      <text class="welcome-text">创建账号</text>
      <text class="sub-text">请填写以下信息完成注册</text>
    </view>
    
    <!-- 表单区域 -->
    <view class="form-section">
      <!-- 用户名输入框 -->
      <view class="input-group">
        <view class="icon-box">
          <uni-icons type="person" size="20" color="#95a5a6"></uni-icons>
        </view>
        <input 
          type="text"
          class="input-field"
          v-model="formData.username"
          placeholder="请输入用户名"
          placeholder-class="placeholder"
        />
      </view>
      
      <!-- 密码输入框 -->
      <view class="input-group">
        <view class="icon-box">
          <uni-icons type="locked" size="20" color="#95a5a6"></uni-icons>
        </view>
        <input 
          :type="showPassword ? 'text' : 'password'"
          class="input-field"
          v-model="formData.password"
          placeholder="请设置密码"
          placeholder-class="placeholder"
        />
      </view>
      
      <!-- 确认密码输入框 -->
      <view class="input-group">
        <view class="icon-box">
          <uni-icons type="locked" size="20" color="#95a5a6"></uni-icons>
        </view>
        <input 
          :type="showPassword ? 'text' : 'password'"
          class="input-field"
          v-model="formData.confirmPassword"
          placeholder="请确认密码"
          placeholder-class="placeholder"
        />
      </view>
      
      <!-- 用户协议 -->
      <view class="agreement-row">
        <label class="agreement-box">
          <checkbox 
            :checked="formData.agreement" 
            @tap="formData.agreement = !formData.agreement"
            color="#3498db"
            class="agreement-checkbox"
          />
          <text class="agreement-text">我已阅读并同意</text>
          <text class="agreement-link" @tap="onViewAgreement">《用户协议》</text>
        </label>
      </view>
      
      <!-- 注册按钮 -->
      <button class="register-btn" @tap="handleRegister">注 册</button>
      
      <!-- 分割线 -->
      <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">或者</text>
        <view class="divider-line"></view>
      </view>
      
      <!-- 登录入口 -->
      <view class="login-section">
        <text class="login-text">已有账号? </text>
        <text class="login-link" @tap="onLogin">立即登录</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive } from 'vue'

// 表单数据
const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  agreement: false
})

// 密码显示状态
const showPassword = ref(false)

// 处理注册
const handleRegister = () => {
  // 表单验证
  if (!formData.username || !formData.password || !formData.confirmPassword) {
    uni.showToast({
      title: '请填写完整注册信息',
      icon: 'none'
    })
    return
  }
  
  if (formData.password !== formData.confirmPassword) {
    uni.showToast({
      title: '两次输入的密码不一致',
      icon: 'none'
    })
    return
  }
  
  if (!formData.agreement) {
    uni.showToast({
      title: '请阅读并同意用户协议',
      icon: 'none'
    })
    return
  }
  
  // TODO: 实现注册逻辑
  console.log('注册信息：', formData)
}

// 查看用户协议
const onViewAgreement = () => {
  // TODO: 跳转到用户协议页面
  uni.navigateTo({
    url: '/pages/agreement/index'
  })
}

// 返回登录
const onLogin = () => {
  uni.navigateBack()
}
</script>

<style>
.register-container {
  min-height: 100vh;
  background-color: #fff;
  padding: 40rpx;
}

.logo-section {
  padding: 60rpx 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.logo-container {
  width: 160rpx;
  height: 160rpx;
  background-color: #3498db;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30rpx;
  box-shadow: 0 12rpx 30rpx rgba(52, 152, 219, 0.3);
}

.logo {
  width: 100rpx;
  height: 100rpx;
}

.welcome-text {
  font-size: 48rpx;
  font-weight: bold;
  color: #222;
  margin-bottom: 20rpx;
}

.sub-text {
  font-size: 28rpx;
  color: #7f8c8d;
}

.form-section {
  padding: 40rpx 0;
}

.input-group {
  position: relative;
  margin-bottom: 40rpx;
}

.icon-box {
  position: absolute;
  left: 30rpx;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
}

.input-field {
  width: 100%;
  height: 100rpx;
  background-color: #f5f7fa;
  border-radius: 24rpx;
  padding: 0 30rpx 0 90rpx;
  font-size: 30rpx;
  color: #333;
}

.placeholder {
  color: #95a5a6;
}

.agreement-row {
  display: flex;
  align-items: center;
  margin-bottom: 50rpx;
}

.agreement-box {
  display: flex;
  align-items: center;
}

.agreement-checkbox {
  transform: scale(0.8);
}

.agreement-text {
  font-size: 28rpx;
  color: #333;
  margin-left: 8rpx;
}

.agreement-link {
  font-size: 28rpx;
  color: #3498db;
}

.register-btn {
  width: 100%;
  height: 100rpx;
  background-color: #3498db;
  color: #fff;
  font-size: 32rpx;
  font-weight: 500;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 60rpx;
  box-shadow: 0 12rpx 30rpx rgba(52, 152, 219, 0.3);
}

.divider {
  display: flex;
  align-items: center;
  margin-bottom: 60rpx;
}

.divider-line {
  flex: 1;
  height: 1px;
  background-color: #ecf0f1;
}

.divider-text {
  padding: 0 30rpx;
  font-size: 26rpx;
  color: #95a5a6;
}

.login-section {
  text-align: center;
}

.login-text {
  font-size: 28rpx;
  color: #7f8c8d;
}

.login-link {
  font-size: 28rpx;
  color: #3498db;
  font-weight: 500;
}
</style> 