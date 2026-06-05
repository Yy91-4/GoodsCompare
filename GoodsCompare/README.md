# GoodsCompare — 全本地化移动端比价 PWA

在 Android 手机上运行的多平台外卖商品比价工具，所有数据和代码都在手机本地，无法律风险。

## 工作原理

- 在 Termux 中运行 Python Flask 后端（localhost:5000）
- 手机浏览器访问作为 PWA 使用（可添加到桌面）
- 输入商品名 → 并行查询三平台移动网页版 → 价格并排展示
- 遇到验证码 → 一键跳转网页验证 → 手动补录价格
- 所有价格记录存入本地 SQLite，支持历史趋势图

## 运行方式

```bash
# 安装 Termux (F-Droid)，然后：
pkg install python sqlite git
pip install flask requests beautifulsoup4 lxml

# 启动服务
cd GoodsCompare
python server.py

# 手机浏览器打开 http://localhost:5000
# 添加到桌面 → 像 App 一样使用
```

## 技术栈

Python Flask + Vanilla JS (PWA) + SQLite + Chart.js

## 功能

- 搜索对比：输入商品名，自动查询三平台价格
- 验证码降级：遇到反爬 → 一键跳转网页 → 手动补录
- 收藏：收藏商品方便回看
- 跳转下单：从比价结果直接跳转到对应平台
- 价格走势：历史价格趋势折线图
- 离线缓存：Service Worker 提供基本离线能力
