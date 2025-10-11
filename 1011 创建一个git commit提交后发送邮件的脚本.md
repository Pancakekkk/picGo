# 🚀 GitHub Actions 自动化：Commit 推送后自动发送邮件通知

## 📖 前言

在日常开发中，我们经常需要及时了解代码仓库的变更情况。虽然 GitHub 提供了邮件通知功能，但有时候我们希望能够自定义通知内容和格式，或者发送到特定的邮箱地址。

本文将介绍如何使用 GitHub Actions 创建一个自动化工作流，当有新的 commit 推送到仓库时，自动发送包含详细信息的邮件通知。

## 🎯 功能特性

- ✅ 自动监听指定分支的推送事件
- ✅ 获取详细的 commit 信息（作者、提交信息、时间等）
- ✅ 统计文件变更情况
- ✅ 发送格式化的邮件通知
- ✅ 支持自定义邮件模板
- ✅ 使用 Gmail SMTP 服务

## 📋 目录

- [工作流配置](#工作流配置)
- [详细步骤](#详细步骤)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [总结](#总结)

## 🔧 工作流配置

首先，我们需要创建一个 GitHub Actions 工作流文件。以下是完整的配置：

```yaml
name: Send Commit Email

on:
  push:
    branches:
      - main   # 监听 main 分支推送，你也可以改成其他分支

jobs:
  send_email:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repo
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # 获取完整历史记录

      - name: Get commit messages
        id: commits
        run: |
          # 获取提交信息
          COMMIT_INFO=$(git log -1 --pretty=format:"%h - %an: %s")
          echo "COMMITS=$COMMIT_INFO" >> $GITHUB_ENV
          
          # 获取文件变更统计（处理可能的浅克隆情况）
          if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
            CHANGES=$(git diff --stat HEAD~1 HEAD)
          else
            CHANGES=$(git diff --stat --cached)
          fi
          echo "CHANGES<<EOF" >> $GITHUB_ENV
          echo "$CHANGES" >> $GITHUB_ENV
          echo "EOF" >> $GITHUB_ENV

      - name: Send mail
        uses: dawidd6/action-send-mail@v3
        with:
          server_address: smtp.gmail.com
          server_port: 465
          username: ${{ secrets.GMAIL_USERNAME }}
          password: ${{ secrets.GMAIL_APP_PASSWORD }}
          subject: "New commit pushed to ${{ github.repository }}"
          body: |
            📧 GitHub Actions 通知
            
            📁 Repository: ${{ github.repository }}
            🌿 Branch: ${{ github.ref_name }}
            👤 Author: ${{ github.actor }}
            🕐 Time: ${{ github.event.head_commit.timestamp }}
            
            📝 Commit Info:
            ${{ env.COMMITS }}
            
            📊 File Changes:
            ${{ env.CHANGES }}
            
            🔗 View on GitHub: ${{ github.event.head_commit.url }}
          to: ${{ secrets.NOTIFICATION_EMAIL }}
          from: GitHub Actions <${{ secrets.GMAIL_USERNAME }}>

```

### 配置说明

让我详细解释一下这个工作流的关键配置：

#### 触发条件
```yaml
on:
  push:
    branches:
      - main   # 监听 main 分支推送，你也可以改成其他分支
```

#### 获取提交信息
```yaml
- name: Get commit messages
  id: commits
  run: |
    # 获取提交信息
    COMMIT_INFO=$(git log -1 --pretty=format:"%h - %an: %s")
    echo "COMMITS=$COMMIT_INFO" >> $GITHUB_ENV
    
    # 获取文件变更统计（处理可能的浅克隆情况）
    if git rev-parse --verify HEAD~1 >/dev/null 2>&1; then
      CHANGES=$(git diff --stat HEAD~1 HEAD)
    else
      CHANGES=$(git diff --stat --cached)
    fi
    echo "CHANGES<<EOF" >> $GITHUB_ENV
    echo "$CHANGES" >> $GITHUB_ENV
    echo "EOF" >> $GITHUB_ENV
```

#### 邮件发送配置
使用 `dawidd6/action-send-mail@v3` 插件发送邮件，支持多种 SMTP 服务。

## 📝 详细步骤

### 步骤 1：创建工作流文件

在仓库中创建 GitHub Actions 工作流文件：

**文件路径：** `.github/workflows/send-commit-email.yml`

#### 方法一：通过 GitHub 网页界面创建

1. 进入你的 GitHub 仓库
2. 点击 "Add file" → "Create new file"
3. 输入路径：`.github/workflows/send-commit-email.yml`
4. 将上面的 YAML 配置复制到文件中
5. 点击 "Commit new file"

![创建工作流文件](https://raw.githubusercontent.com/Pancakekkk/picGo/main/20251011153629178.png)

#### 方法二：通过本地命令行创建

```bash
# 创建目录结构
mkdir -p .github/workflows

# 进入目录
cd .github/workflows

# 创建文件
touch send-commit-email.yml

# 编辑文件并添加配置内容
```

### 步骤 2：配置 GitHub Secrets

为了安全地存储敏感信息（如邮箱密码），我们需要使用 GitHub Secrets：

1. 进入你的 GitHub 仓库
2. 点击 "Settings" → "Secrets and variables" → "Actions"
3. 点击 "New repository secret"

#### 需要添加的 Secrets：

| Secret 名称 | 说明 | 示例值 |
|------------|------|--------|
| `GMAIL_USERNAME` | 你的 Gmail 地址 | `your-email@gmail.com` |
| `GMAIL_APP_PASSWORD` | Gmail 应用专用密码 | `your-app-password` |
| `NOTIFICATION_EMAIL` | 接收通知的邮箱地址 | `notification@example.com` |

#### 获取 Gmail 应用专用密码

1. 访问 [Google 账号安全设置](https://myaccount.google.com/apppasswords)
2. 选择 "应用专用密码"
3. 选择 "邮件" 和你的设备
4. 生成密码后，**记得删除字母之间的空格**，否则 Action 运行会报错

![Gmail 应用密码设置](https://raw.githubusercontent.com/Pancakekkk/picGo/main/20251011154420305.png)

### 步骤 3：测试工作流

1. 向 `main` 分支推送一个 commit
2. 进入仓库的 "Actions" 页面
3. 查看工作流执行状态
4. 检查邮箱是否收到通知

## ⚙️ 配置说明

### 自定义邮件模板

你可以修改邮件内容模板，添加更多信息：

```yaml
body: |
  🎉 代码更新通知
  
  📁 仓库：${{ github.repository }}
  🌿 分支：${{ github.ref_name }}
  👤 作者：${{ github.actor }}
  🕐 时间：${{ github.event.head_commit.timestamp }}
  
  📝 提交信息：
  ${{ env.COMMITS }}
  
  📊 文件变更：
  ${{ env.CHANGES }}
  
  🔗 查看详情：${{ github.event.head_commit.url }}
  
  ---
  🤖 此邮件由 GitHub Actions 自动发送
```

### 监听多个分支

如果你需要监听多个分支：

```yaml
on:
  push:
    branches:
      - main
      - develop
      - release/*
```

### 使用其他邮件服务

除了 Gmail，你还可以使用其他 SMTP 服务：

```yaml
# 使用 QQ 邮箱
server_address: smtp.qq.com
server_port: 587

# 使用 163 邮箱
server_address: smtp.163.com
server_port: 465
```

## ❓ 常见问题

### Q1: 工作流没有触发怎么办？

**A:** 检查以下几点：
- 确认文件路径正确：`.github/workflows/send-commit-email.yml`
- 确认推送的分支名称与配置中的分支名称一致
- 检查 Actions 页面是否有权限问题

### Q2: 邮件发送失败怎么办？

**A:** 常见原因和解决方案：
- **密码错误**：确认使用的是应用专用密码，不是登录密码
- **空格问题**：应用密码中的空格需要删除
- **权限问题**：确认 Gmail 账号已开启两步验证
- **网络问题**：检查 SMTP 服务器地址和端口是否正确

### Q3: 如何自定义邮件接收者？

**A:** 修改 `to` 字段：
```yaml
to: ${{ secrets.NOTIFICATION_EMAIL }}, another@example.com
```

### Q4: 可以发送 HTML 格式的邮件吗？

**A:** 可以，在 `body` 中使用 HTML 标签：
```yaml
body: |
  <h2>🎉 代码更新通知</h2>
  <p><strong>仓库：</strong>${{ github.repository }}</p>
  <p><strong>分支：</strong>${{ github.ref_name }}</p>
  <!-- 更多 HTML 内容 -->
```

## 🎉 总结

通过本文的介绍，你已经学会了如何：

1. ✅ 创建 GitHub Actions 工作流
2. ✅ 配置邮件发送功能
3. ✅ 设置 GitHub Secrets
4. ✅ 自定义邮件模板
5. ✅ 处理常见问题

这个自动化方案可以帮助你：
- 📧 及时了解代码变更
- 🔔 提高团队协作效率
- 🛡️ 增强项目监控能力
- 🎨 自定义通知格式

如果你觉得这篇文章对你有帮助，欢迎点赞、收藏和分享！有任何问题也可以在评论区留言讨论。

---

**标签：** `GitHub Actions` `自动化` `邮件通知` `DevOps` `CI/CD`