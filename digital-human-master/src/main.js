import {
	createSSRApp
} from "vue";
import App from "./App.vue";

// 引入uni-ui组件
import uniIcons from '@dcloudio/uni-ui/lib/uni-icons/uni-icons.vue'

export function createApp() {
	const app = createSSRApp(App);
	
	// 注册全局组件
	app.component('uni-icons', uniIcons)
	
	// 全局路由拦截
	const list = ["navigateTo", "redirectTo", "reLaunch", "switchTab"];
	list.forEach(item => {
		uni.addInterceptor(item, {
			invoke(e) {
				console.log('路由拦截', e)
				return e
			},
			success(e) {
				console.log('路由成功', e)
			},
			fail(err) {
				console.log('路由失败', err)
			}
		})
	})
	
	return {
		app,
	};
}

