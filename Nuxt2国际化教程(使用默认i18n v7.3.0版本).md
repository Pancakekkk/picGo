# Nuxt2国际化教程(使用默认i18n v7.3.0版本)

注意我这里使用的nuxt版本是**nuxt": "^2.15.8**

vue是**"^2.7.10"**

### 1.下载7.3.0版本的nuxt I18n

``` 
npm i @nuxtjs/i18n v7.3.0
```
> nuxt2 npm安装下载时需注意要指定版本号，不然默认下载的是nuxt3版本会与项目冲突

在pack.json中可以看到

```
@nuxtjs/i18n": "^7.3.0
```

## 2.在nuxt.config.js中的modules添加'@nuxtjs/i18n'  

```
'@nuxtjs/i18n'
```

![image-20240710100106589](https://raw.githubusercontent.com/Pancakekkk/PicGoHouse/master/image-20240710100106589.png?token=A6XRFMAAWSE5OHUXORXCLL3GTXZ4K)

### 3.创建语言文件目录

##### 1）在根目录下新建locales文件夹,创建语言js文件,如en.js

![image-20240710105249936](https://raw.githubusercontent.com/Pancakekkk/PicGoHouse/master/image-20240710105249936.png?token=A6XRFMAB7P3JTLOY52YH6X3GTXZ4M)

js文件内的内容如下(以英文en为例)：

```
export default {
  welcome: 'Welcome to our website'
}
```

> 字段名**"welcome"**在每个js文件中需要保持一样,这样页面才能正常渲染

##### 2) 在nuxt.config.js中引入文件

```import frLocale from './locales/fr'
import frLocale from './locales/fr'
import geLocale from './locales/ge'
import enLocale from './locales/en'
```

##### 3) 在export default中引入以下代码

```
i18n: {
    locales: [
      { code: 'en', iso: 'en-US', name: 'English' },
      { code: 'ge', iso: 'de-GM', name: 'Germany' },
      { code: 'fr', iso: 'fr-CA', name: 'Franch' }
    ],
    defaultLocale: 'en',
    strategy: 'prefix_except_default',
    vueI18n: {
      fallbackLocale: 'en',   //默认展示英文
      messages: {
        en: { ...enLocale },
        ge: { ...geLocale },
        fr: { ...frLocale }
      }
    }
  }
```

> locales数组对象中**code**字段是必须的
>
> **name**是用作页面中渲染的切换语言时展示的文字，**messages**中是引用的语言包文件，**defaultLocale**定义默认展示的语言

### 4.在页面中添加下拉按钮

##### 1）引入vue工具类

```
import { ref, onMounted getCurrentInstance } from 'vue'
const { proxy } = getCurrentInstance()
const { $i18n } = proxy
const language = ref(null)
```

##### 2）添加页面组件

```
<el-dropdown trigger="click">
        <div>
          <svg t="1718271463080" class="icon" viewBox="0 0 1024 1024" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="2936" width="30" height="30"><path d="M819.2 316.416V819.2H316.416c20.992 59.392 77.312 102.4 144.384 102.4h460.8V460.8c0-66.56-43.008-122.88-102.4-144.384zM363.52 441.344h89.6l-45.056-97.28-44.544 97.28z" fill="#677BA5" p-id="2937" /><path d="M563.2 102.4H102.4v460.8c0 84.992 68.608 153.6 153.6 153.6h460.8V256c0-84.992-68.608-153.6-153.6-153.6z m-43.008 482.304l-36.352-78.336H334.336l-35.84 78.336H235.52l173.056-379.392 176.128 379.392h-64z" fill="#677BA5" p-id="2938" /></svg>
        </div>
        <el-dropdown-menu slot="dropdown">
          <el-dropdown-item v-for="locale in $i18n.locales" :key="locale.code" :disabled="language===locale.code" :command="locale.code">
            <span :style="language===locale.code?'color: #ccc;':''" @click="setLanguageHandler(locale.code)">{{ locale.name }}</span>
          </el-dropdown-item>
        </el-dropdown-menu>
      </el-dropdown>
```

##### 3）页面中显示多语言

```
{{ $t('welcome') }}
```

##### 4）切换语言方法

```
//页面加载时默认先获取网页缓存的语言
onMounted(() => {
  language.value = localStorage.getItem('language') || 'en'
  $i18n.setLocale(language)
})
// 切换语言
const setLanguageHandler = (val) => {
  language.value = val
  localStorage.setItem('language', val)//这里做了一个本地缓存，用户离开重新进入页面默认加载上次的语言
  $i18n.setLocale(val)
  location.reload()
}
```

如果需要地址跳转的话需要使用**“localePath“**跳转保留当前的语言

```
router.push(({ path: proxy.localePath('/') + menu }))
```

#### 这样就完成了在nuxt2项目中切换多语言的功能！

