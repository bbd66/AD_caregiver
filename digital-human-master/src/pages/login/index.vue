<template>
  <view class="login-container">
    <!-- Logo区域 -->
    <view class="logo-section">
      <view class="logo-container">
        <image src="/src/static/logo.png" mode="aspectFit" class="logo"></image>
      </view>
      <text class="welcome-text">欢迎回来</text>
      <text class="sub-text">请登录您的账号继续</text>
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
          placeholder="用户名/手机号"
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
          placeholder="密码"
          placeholder-class="placeholder"
        />
      </view>
      
      <!-- 记住密码和忘记密码 -->
      <view class="options-row">
        <label class="remember-box">
          <checkbox 
            :checked="formData.remember" 
            @tap="formData.remember = !formData.remember"
            color="#3498db"
            class="remember-checkbox"
          />
          <text class="remember-text">记住我</text>
        </label>
        <text class="forgot-text" @tap="onForgotPassword">忘记密码?</text>
      </view>
      
      <!-- 登录按钮 -->
      <button class="login-btn" @tap="handleLogin">登 录</button>
      
      <!-- 分割线 -->
      <view class="divider">
        <view class="divider-line"></view>
        <text class="divider-text">或者</text>
        <view class="divider-line"></view>
      </view>
      
      <!-- 注册入口 -->
      <view class="signup-text">
        <text>还没有账号? </text>
        <text class="signup-link" @click="goToRegister">立即注册</text>
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
  remember: false
})

// 密码显示状态
const showPassword = ref(false)

// 处理登录
const handleLogin = () => {
  if (!formData.username || !formData.password) {
    uni.showToast({
      title: '请输入用户名和密码',
      icon: 'none'
    })
    return
  }
  
  // 显示加载提示
  uni.showLoading({
    title: '登录中...',
    mask: true
  })
  
  // 模拟登录API调用
  setTimeout(() => {
    uni.hideLoading()
    
    // 模拟登录成功
    uni.reLaunch({
      url: '/pages/index/index',
      success: () => {
        console.log('跳转到主页成功')
        // 可以在这里存储登录状态
        uni.setStorageSync('isLoggedIn', true)
        uni.setStorageSync('userInfo', {
          username: formData.username
        })
      },
      fail: (err) => {
        console.error('跳转失败', err)
        uni.showToast({
          title: '跳转失败，请重试',
          icon: 'none'
        })
      }
    })
  }, 1500)
}

// 忘记密码
const onForgotPassword = () => {
  uni.navigateTo({
    url: '/pages/forgot-password/index'
  })
}

// 跳转到注册页面
const goToRegister = () => {
  console.log('点击注册按钮')
  try {
    uni.navigateTo({
      url: '/pages/register/index',
      success: (res) => {
        console.log('跳转成功', res)
      },
      fail: (err) => {
        console.error('跳转失败', err)
        // 如果navigateTo失败，尝试使用reLaunch
        uni.reLaunch({
          url: '/pages/register/index'
        })
      }
    })
  } catch (error) {
    console.error('跳转异常', error)
  }
}
</script>

<style>
.login-container {
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

.options-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 50rpx;
}

.remember-box {
  display: flex;
  align-items: center;
}

.remember-checkbox {
  transform: scale(0.8);
}

.remember-text {
  font-size: 28rpx;
  color: #333;
  margin-left: 8rpx;
}

.forgot-text {
  font-size: 28rpx;
  color: #3498db;
}

.login-btn {
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

.signup-text {
  text-align: center;
  font-size: 28rpx;
  color: #7f8c8d;
}

.signup-link {
  color: #3498db;
  font-weight: 500;
}
</style> 