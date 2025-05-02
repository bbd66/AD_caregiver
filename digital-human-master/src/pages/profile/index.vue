<template>
  <view class="profile-container">
    <!-- 顶部导航栏 -->
    <view class="header">
      <view class="header-left" @tap="goBack">
        <uni-icons type="left" size="24" color="#333"></uni-icons>
      </view>
      <view class="header-title">个人信息</view>
      <view class="header-right">
        <view class="icon-wrapper"></view>
      </view>
    </view>

    <!-- 用户信息卡片 -->
    <view class="profile-card">
      <view class="avatar-section">
        <view class="avatar-wrapper">
          <image src="/src/static/logo.png" mode="aspectFill" class="avatar-image"></image>
        </view>
      </view>
      
      <view class="user-info">
        <text class="username">{{ userInfo.username || '未登录' }}</text>
        <text class="user-id">ID: {{ userInfo.id || 'N/A' }}</text>
      </view>
    </view>

    <!-- 信息列表 -->
    <view class="info-list">
      <view class="list-item" @tap="editUsername">
        <view class="item-label">用户名</view>
        <view class="item-content">
          <text>{{ userInfo.username }}</text>
          <uni-icons type="right" size="18" color="#999"></uni-icons>
        </view>
      </view>
      
      <view class="list-item" @tap="editPhone">
        <view class="item-label">手机号</view>
        <view class="item-content">
          <text>{{ userInfo.phone || '未绑定' }}</text>
          <uni-icons type="right" size="18" color="#999"></uni-icons>
        </view>
      </view>
      
      <view class="list-item" @tap="editEmail">
        <view class="item-label">邮箱</view>
        <view class="item-content">
          <text>{{ userInfo.email || '未绑定' }}</text>
          <uni-icons type="right" size="18" color="#999"></uni-icons>
        </view>
      </view>
    </view>

    <!-- 安全设置 -->
    <view class="section-title">安全设置</view>
    <view class="info-list">
      <view class="list-item" @tap="changePassword">
        <view class="item-label">修改密码</view>
        <view class="item-content">
          <uni-icons type="right" size="18" color="#999"></uni-icons>
        </view>
      </view>
    </view>

    <!-- 退出登录按钮 -->
    <view class="action-buttons">
      <button class="logout-btn" @tap="logout">退出登录</button>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

// 用户信息
const userInfo = reactive({
  username: '',
  id: '',
  phone: '',
  email: ''
})

// 返回上一页
const goBack = () => {
  uni.navigateBack()
}

// 退出登录
const logout = () => {
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
}

// 编辑用户名
const editUsername = () => {
  uni.showModal({
    title: '修改用户名',
    editable: true,
    placeholderText: userInfo.username,
    success: (res) => {
      if (res.confirm && res.content) {
        userInfo.username = res.content
        // 更新存储的用户信息
        const storedInfo = uni.getStorageSync('userInfo') || {}
        storedInfo.username = res.content
        uni.setStorageSync('userInfo', storedInfo)
        
        uni.showToast({
          title: '修改成功',
          icon: 'success'
        })
      }
    }
  })
}

// 编辑手机号
const editPhone = () => {
  uni.showModal({
    title: '修改手机号',
    editable: true,
    placeholderText: userInfo.phone || '请输入手机号',
    success: (res) => {
      if (res.confirm && res.content) {
        userInfo.phone = res.content
        // 更新存储的用户信息
        const storedInfo = uni.getStorageSync('userInfo') || {}
        storedInfo.phone = res.content
        uni.setStorageSync('userInfo', storedInfo)
        
        uni.showToast({
          title: '修改成功',
          icon: 'success'
        })
      }
    }
  })
}

// 编辑邮箱
const editEmail = () => {
  uni.showModal({
    title: '修改邮箱',
    editable: true,
    placeholderText: userInfo.email || '请输入邮箱',
    success: (res) => {
      if (res.confirm && res.content) {
        userInfo.email = res.content
        // 更新存储的用户信息
        const storedInfo = uni.getStorageSync('userInfo') || {}
        storedInfo.email = res.content
        uni.setStorageSync('userInfo', storedInfo)
        
        uni.showToast({
          title: '修改成功',
          icon: 'success'
        })
      }
    }
  })
}

// 修改密码
const changePassword = () => {
  uni.showToast({
    title: '密码修改功能开发中',
    icon: 'none'
  })
}

// 加载用户信息
onMounted(() => {
  const storedInfo = uni.getStorageSync('userInfo')
  if (storedInfo) {
    Object.assign(userInfo, storedInfo)
    if (!userInfo.id) {
      userInfo.id = 'U' + Math.floor(Math.random() * 1000000).toString().padStart(6, '0')
      
      // 保存生成的ID
      const updatedInfo = {...storedInfo, id: userInfo.id}
      uni.setStorageSync('userInfo', updatedInfo)
    }
  }
})
</script>

<style>
.profile-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding-bottom: 40rpx;
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
}

.header-left {
  width: 60rpx;
  height: 60rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #333;
}

.header-right {
  width: 60rpx;
}

/* 用户信息卡片 */
.profile-card {
  background-color: #fff;
  border-radius: 20rpx;
  margin: 30rpx;
  padding: 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.05);
}

.avatar-section {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 30rpx;
}

.avatar-wrapper {
  width: 160rpx;
  height: 160rpx;
  border-radius: 80rpx;
  background-color: #3498db;
  overflow: hidden;
  box-shadow: 0 6rpx 20rpx rgba(52, 152, 219, 0.2);
}

.avatar-image {
  width: 100%;
  height: 100%;
}

.user-info {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.username {
  font-size: 40rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
}

.user-id {
  font-size: 26rpx;
  color: #95a5a6;
}

/* 信息列表 */
.info-list {
  background-color: #fff;
  border-radius: 20rpx;
  margin: 0 30rpx 30rpx;
  overflow: hidden;
}

.list-item {
  height: 110rpx;
  padding: 0 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1rpx solid #f0f0f0;
}

.list-item:last-child {
  border-bottom: none;
}

.item-label {
  font-size: 30rpx;
  color: #333;
}

.item-content {
  display: flex;
  align-items: center;
}

.item-content text {
  font-size: 30rpx;
  color: #666;
  margin-right: 20rpx;
}

.section-title {
  font-size: 28rpx;
  color: #95a5a6;
  padding: 0 30rpx;
  margin: 40rpx 0 20rpx;
}

/* 退出登录按钮 */
.action-buttons {
  padding: 40rpx 30rpx;
}

.logout-btn {
  width: 100%;
  height: 90rpx;
  line-height: 90rpx;
  background-color: #fff;
  border: 1rpx solid #e74c3c;
  color: #e74c3c;
  font-size: 32rpx;
  border-radius: 45rpx;
}
</style> 