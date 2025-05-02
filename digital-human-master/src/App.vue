<script>
export default {
  onLaunch: function () {
    console.log('App Launch')
    
    // 检查是否已登录
    const isLoggedIn = uni.getStorageSync('isLoggedIn')
    const pages = getCurrentPages()
    
    if (!pages.length) {
      if (isLoggedIn) {
        // 已登录，跳转到主页
        uni.reLaunch({
          url: '/pages/index/index'
        })
      } else {
        // 未登录，跳转到登录页
        uni.reLaunch({
          url: '/pages/login/index'
        })
      }
    }
  },
  onShow: function () {
    console.log('App Show')
  },
  onHide: function () {
    console.log('App Hide')
  },
}
</script>

<style>
/*每个页面公共css */
uni-page-body {
  height: 100%;
}

/* 全局颜色定义 */
page {
  --primary-color: #3498db;
  --secondary-color: #2980b9;
  --text-color: #333333;
  --text-color-light: #7f8c8d;
  --bg-color: #f5f7fa;
  --bg-color-light: #ffffff;
}

/* 全局阴影样式 */
.shadow {
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.1);
}
</style>
