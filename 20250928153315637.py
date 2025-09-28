#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
掘金文章抓取器 - 最终优化版本
功能：
1. 抓取掘金文章内容并转换为Markdown格式
2. 获取文章完整元数据（作者、点赞、评论、收藏等）
3. 抓取并排序评论（按点赞数排序，限制10条）
4. 获取评论下的子评论（最多5条）
5. 生成格式化的Markdown文件

作者：AI Assistant
版本：2.0 Final
"""

import requests
from bs4 import BeautifulSoup
import html_to_markdown
import sys
import re
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Dict, List, Optional, Tuple


class JuejinScraper:
    """掘金文章抓取器"""
    
    def __init__(self, headless: bool = True, max_comments: int = 10, max_replies: int = 5):
        """
        初始化抓取器
        
        Args:
            headless: 是否使用无头模式
            max_comments: 最大评论数量
            max_replies: 每条评论下最大回复数量
        """
        self.headless = headless
        self.max_comments = max_comments
        self.max_replies = max_replies
        self.driver = None
    
    def setup_driver(self) -> webdriver.Chrome:
        """设置并返回Chrome WebDriver"""
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return driver
    
    def load_comments(self, driver: webdriver.Chrome) -> None:
        """加载指定数量的评论"""
        print(f"开始加载评论，目标数量：{self.max_comments}")
        
        # 滚动到页面底部以加载初始评论
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        comment_count = 0
        attempts = 0
        max_attempts = 20  # 最大尝试次数
        
        while comment_count < self.max_comments and attempts < max_attempts:
            try:
                # 检查当前评论数量
                current_comments = driver.find_elements(By.CSS_SELECTOR, ".comment-card.comment-item")
                comment_count = len(current_comments)
                
                if comment_count >= self.max_comments:
                    print(f"已达到目标评论数量：{comment_count}")
                    break
                
                # 查找并点击"加载更多"按钮
                load_more_buttons = driver.find_elements(By.CSS_SELECTOR, ".fetch-more-comment")
                if load_more_buttons:
                    # 点击最后一个加载更多按钮
                    last_button = load_more_buttons[-1]
                    if last_button.is_displayed() and last_button.is_enabled():
                        driver.execute_script("arguments[0].click();", last_button)
                        print(f"点击加载更多，当前评论数：{comment_count}")
                        time.sleep(3)  # 增加等待时间
                    else:
                        print("加载更多按钮不可见或不可点击")
                        break
                else:
                    print("没有找到更多评论加载按钮")
                    break
                
                attempts += 1
                
            except Exception as e:
                print(f"加载评论时出错：{e}")
                attempts += 1
                time.sleep(1)
        
        print(f"评论加载完成，共找到 {comment_count} 条评论")
    
    def expand_replies(self, driver: webdriver.Chrome, comment_element) -> None:
        """展开评论下的回复"""
        try:
            # 查找回复按钮
            reply_buttons = comment_element.find_elements(By.CSS_SELECTOR, ".reply-btn, .show-replies")
            if reply_buttons:
                for button in reply_buttons:
                    if button.is_displayed() and button.is_enabled():
                        try:
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(1)
                            print("展开回复成功")
                        except Exception as e:
                            print(f"展开回复失败：{e}")
                        break
        except Exception as e:
            print(f"展开回复时出错：{e}")
    
    def extract_replies(self, comment_element) -> List[Dict]:
        """提取评论下的回复"""
        replies = []
        try:
            # 查找回复元素
            reply_elements = comment_element.find_elements(By.CSS_SELECTOR, ".reply-item, .sub-comment")
            
            for i, reply_element in enumerate(reply_elements[:self.max_replies]):
                try:
                    # 提取回复作者
                    reply_author = self._extract_reply_author(reply_element)
                    
                    # 提取回复内容
                    reply_content = self._extract_reply_content(reply_element)
                    
                    # 提取回复时间
                    reply_time = self._extract_reply_time(reply_element)
                    
                    # 提取回复点赞数
                    reply_likes = self._extract_reply_likes(reply_element)
                    
                    replies.append({
                        'author': reply_author,
                        'content': reply_content,
                        'time': reply_time,
                        'likes': reply_likes
                    })
                    
                except Exception as e:
                    print(f"处理第 {i+1} 条回复时出错：{e}")
                    continue
                    
        except Exception as e:
            print(f"提取回复失败：{e}")
        
        return replies
    
    def _extract_reply_author(self, reply_element) -> str:
        """提取回复作者名"""
        try:
            author_elements = reply_element.find_elements(By.CSS_SELECTOR, ".username .name, .reply-author")
            return author_elements[0].text.strip() if author_elements else "未知用户"
        except:
            return "未知用户"
    
    def _extract_reply_content(self, reply_element) -> str:
        """提取回复内容"""
        try:
            content_elements = reply_element.find_elements(By.CSS_SELECTOR, ".reply-content, .content")
            content = content_elements[0].text.strip() if content_elements else ""
            return content.replace('\n', '\n> ')
        except:
            return ""
    
    def _extract_reply_time(self, reply_element) -> str:
        """提取回复时间"""
        try:
            time_elements = reply_element.find_elements(By.CSS_SELECTOR, "*[class*='time']")
            return time_elements[0].text.strip() if time_elements else "未知时间"
        except:
            return "未知时间"
    
    def _extract_reply_likes(self, reply_element) -> int:
        """提取回复点赞数"""
        try:
            like_elements = reply_element.find_elements(By.CSS_SELECTOR, "*[class*='digg'], *[class*='like']")
            if like_elements:
                like_text = like_elements[0].text.strip()
                like_match = re.search(r'\d+', like_text)
                return int(like_match.group()) if like_match else 0
            return 0
        except:
            return 0
    
    def extract_comments(self, driver: webdriver.Chrome) -> List[Dict]:
        """提取评论数据"""
        print("开始提取评论信息...")
        comments_data = []
        
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".comment-card.comment-item"))
            )
            
            comment_elements = driver.find_elements(By.CSS_SELECTOR, ".comment-card.comment-item")
            print(f"找到 {len(comment_elements)} 条评论")
            
            for i, comment_element in enumerate(comment_elements[:self.max_comments]):
                try:
                    # 展开回复
                    self.expand_replies(driver, comment_element)
                    
                    # 提取作者名
                    author_element = comment_element.find_element(By.CSS_SELECTOR, ".username .name")
                    author = author_element.text.strip()
                    
                    # 提取评论内容
                    content_element = comment_element.find_element(By.CSS_SELECTOR, ".comment-content .content")
                    content = content_element.text.strip().replace('\n', '\n> ')
                    
                    # 提取时间
                    time_text = self._extract_comment_time(comment_element)
                    
                    # 提取点赞数 - 优化提取逻辑
                    like_count = self._extract_comment_likes_optimized(comment_element)
                    
                    # 提取回复数 - 优化提取逻辑
                    reply_count = self._extract_comment_replies_optimized(comment_element)
                    
                    # 提取子评论
                    replies = self.extract_replies(comment_element)
                    
                    comments_data.append({
                        'author': author,
                        'content': content,
                        'time': time_text,
                        'likes': like_count,
                        'replies': reply_count,
                        'sub_replies': replies
                    })
                    
                    print(f"处理第 {i+1} 条评论：{author} - 点赞:{like_count} 回复:{reply_count} 子回复:{len(replies)}")
                    
                except Exception as e:
                    print(f"处理第 {i+1} 条评论时出错：{e}")
                    continue
                    
        except Exception as e:
            print(f"提取评论失败：{e}")
        
        return comments_data
    
    def _extract_comment_time(self, comment_element) -> str:
        """提取评论时间"""
        try:
            time_elements = comment_element.find_elements(By.CSS_SELECTOR, "*[class*='time']")
            return time_elements[0].text.strip() if time_elements else "未知时间"
        except:
            return "未知时间"
    
    def _extract_comment_likes_optimized(self, comment_element) -> int:
        """优化提取评论点赞数"""
        try:
            # 方法1：查找点赞按钮上的数字
            like_buttons = comment_element.find_elements(By.CSS_SELECTOR, ".like-btn, .digg-btn, [class*='like'], [class*='digg']")
            for button in like_buttons:
                try:
                    # 查找按钮内的数字文本
                    button_text = button.text.strip()
                    if button_text and button_text.isdigit():
                        return int(button_text)
                    
                    # 查找按钮的data属性
                    data_likes = button.get_attribute("data-likes") or button.get_attribute("data-count")
                    if data_likes and data_likes.isdigit():
                        return int(data_likes)
                        
                except:
                    continue
            
            # 方法2：查找包含点赞数的span元素
            like_spans = comment_element.find_elements(By.CSS_SELECTOR, "span[class*='count'], span[class*='num'], span[class*='like']")
            for span in like_spans:
                try:
                    span_text = span.text.strip()
                    if span_text and span_text.isdigit():
                        return int(span_text)
                except:
                    continue
            
            # 方法3：查找所有包含数字的文本，判断是否为点赞数
            all_text = comment_element.text
            like_patterns = [
                r'点赞\s*(\d+)',
                r'(\d+)\s*赞',
                r'(\d+)\s*like',
                r'like\s*(\d+)'
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            return 0
            
        except Exception as e:
            print(f"提取点赞数时出错：{e}")
            return 0
    
    def _extract_comment_replies_optimized(self, comment_element) -> int:
        """优化提取评论回复数"""
        try:
            # 方法1：查找回复按钮上的数字
            reply_buttons = comment_element.find_elements(By.CSS_SELECTOR, ".reply-btn, .show-replies, [class*='reply']")
            for button in reply_buttons:
                try:
                    button_text = button.text.strip()
                    if button_text and button_text.isdigit():
                        return int(button_text)
                    
                    # 查找按钮的data属性
                    data_replies = button.get_attribute("data-replies") or button.get_attribute("data-count")
                    if data_replies and data_replies.isdigit():
                        return int(data_replies)
                        
                except:
                    continue
            
            # 方法2：查找包含回复数的span元素
            reply_spans = comment_element.find_elements(By.CSS_SELECTOR, "span[class*='count'], span[class*='num'], span[class*='reply']")
            for span in reply_spans:
                try:
                    span_text = span.text.strip()
                    if span_text and span_text.isdigit():
                        return int(span_text)
                except:
                    continue
            
            # 方法3：查找所有包含数字的文本，判断是否为回复数
            all_text = comment_element.text
            reply_patterns = [
                r'回复\s*(\d+)',
                r'(\d+)\s*回复',
                r'(\d+)\s*reply',
                r'reply\s*(\d+)'
            ]
            
            for pattern in reply_patterns:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    return int(match.group(1))
            
            return 0
            
        except Exception as e:
            print(f"提取回复数时出错：{e}")
            return 0
    
    def extract_author_info(self, driver: webdriver.Chrome) -> Tuple[str, str]:
        """提取作者信息"""
        print("提取作者信息...")
        
        # 方法1：查找所有用户链接
        try:
            user_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/user/']")
            print(f"找到 {len(user_links)} 个用户链接")
            
            for link in user_links:
                try:
                    href = link.get_attribute("href")
                    if href and "/user/" in href and "posts" in href:
                        try:
                            name_element = link.find_element(By.CSS_SELECTOR, ".name, .username")
                            author_name = name_element.text.strip()
                            if author_name:
                                if href.startswith('/'):
                                    href = "https://juejin.cn" + href
                                print(f"找到作者：{author_name}")
                                return author_name, href
                        except:
                            continue
                except:
                    continue
        except Exception as e:
            print(f"方法1提取作者信息失败：{e}")
        
        # 方法2：备用方法
        try:
            author_element = driver.find_element(By.CSS_SELECTOR, ".user-name, .username, .author-name")
            author_name = author_element.text.strip()
            print(f"备用方法找到作者：{author_name}")
            return author_name, ""
        except Exception as e:
            print(f"备用方法也失败：{e}")
            return "未知作者", ""
    
    def extract_article_stats(self, driver: webdriver.Chrome) -> Dict[str, int]:
        """提取文章统计数据（点赞、评论、收藏）"""
        print("提取文章统计数据...")
        stats = {'likes': 0, 'comments': 0, 'collects': 0}
        
        try:
            panel_buttons = driver.find_elements(By.CSS_SELECTOR, ".panel-btn.with-badge")
            print(f"找到 {len(panel_buttons)} 个统计按钮")
            
            for button in panel_buttons:
                try:
                    badge_value = button.get_attribute("badge")
                    if not badge_value:
                        continue
                    
                    svg_element = button.find_element(By.CSS_SELECTOR, "svg")
                    svg_class = svg_element.get_attribute("class")
                    
                    if "icon-zan" in svg_class:
                        stats['likes'] = int(badge_value)
                        print(f"点赞数：{stats['likes']}")
                    elif "icon-comment" in svg_class:
                        stats['comments'] = int(badge_value)
                        print(f"评论数：{stats['comments']}")
                    elif "icon-collect" in svg_class:
                        stats['collects'] = int(badge_value)
                        print(f"收藏数：{stats['collects']}")
                        
                except Exception as e:
                    print(f"处理统计按钮时出错：{e}")
                    continue
            
        except Exception as e:
            print(f"提取统计数据失败：{e}")
        
        return stats
    
    def extract_additional_metadata(self, driver: webdriver.Chrome) -> Dict[str, str]:
        """提取额外的元数据"""
        metadata = {}
        
        # 提取发表时间
        try:
            time_element = driver.find_element(By.CSS_SELECTOR, "*[class*='time']")
            metadata['publish_time'] = time_element.text.strip()
            print(f"发表时间：{metadata['publish_time']}")
        except:
            metadata['publish_time'] = "未知时间"
        
        # 提取阅读时长
        try:
            page_text = driver.execute_script("return document.body.innerText;")
            read_match = re.search(r'阅读(\d+分钟)', page_text)
            metadata['read_time'] = read_match.group(1) if read_match else "未知"
            print(f"阅读时长：{metadata['read_time']}")
        except:
            metadata['read_time'] = "未知"
        
        # 提取专栏名称
        try:
            column_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '专栏')]")
            if column_elements:
                for elem in column_elements:
                    text = elem.text.strip()
                    if '专栏' in text and len(text) < 50:
                        metadata['column'] = text
                        break
                else:
                    metadata['column'] = "无专栏"
            else:
                metadata['column'] = "无专栏"
            print(f"专栏名称：{metadata['column']}")
        except:
            metadata['column'] = "无专栏"
        
        return metadata
    
    def generate_markdown(self, article_data: Dict) -> str:
        """生成Markdown内容"""
        md_content = []
        
        # 标题
        md_content.append(f"# {article_data['title']}\n")
        
        # 作者信息
        if article_data['author_link']:
            md_content.append(f"**作者：** [{article_data['author_name']}]({article_data['author_link']})\n")
        else:
            md_content.append(f"**作者：** {article_data['author_name']}\n")
        
        # 文章信息表格
        md_content.append("## 📊 文章信息\n")
        md_content.append("| 项目 | 内容 |")
        md_content.append("|------|------|")
        md_content.append(f"| 发表时间 | {article_data['publish_time']} |")
        md_content.append(f"| 点赞数 | {article_data['likes']} |")
        md_content.append(f"| 评论数 | {article_data['comments']} |")
        md_content.append(f"| 收藏数 | {article_data['collects']} |")
        md_content.append(f"| 阅读时长 | {article_data['read_time']} |")
        md_content.append(f"| 专栏名称 | {article_data['column']} |")
        md_content.append(f"| 原文链接 | [{article_data['title']}]({article_data['url']}) |\n")
        
        md_content.append("---\n")
        
        # 文章内容
        md_content.append("## 📝 文章内容\n")
        md_content.append(article_data['content'])
        
        # 精选评论
        if article_data['comments_data']:
            md_content.append("\n\n---\n")
            md_content.append("## 💬 精选评论\n")
            
            # 按点赞数排序并取前10条
            sorted_comments = sorted(article_data['comments_data'], key=lambda x: x['likes'], reverse=True)
            top_comments = sorted_comments[:self.max_comments]
            
            for comment in top_comments:
                # 构建评论标题，始终显示点赞和回复数
                title_parts = [
                    comment['author'],
                    f"👍 {comment['likes']}",
                    f"💬 {comment['replies']}",
                    comment['time']
                ]
                comment_title = " ".join(title_parts)
                md_content.append(f"### {comment_title}\n")
                md_content.append(f"{comment['content']}\n")
                
                # 显示子评论
                if comment['sub_replies']:
                    md_content.append("\n**回复：**\n")
                    for reply in comment['sub_replies']:
                        # 始终显示子评论的点赞数
                        reply_title = f"{reply['author']} (👍 {reply['likes']}) - {reply['time']}"
                        
                        md_content.append(f"**{reply_title}**\n")
                        md_content.append(f"> {reply['content']}\n")
                
                md_content.append("\n---\n")
        
        return "\n".join(md_content)
    
    def save_article(self, url: str) -> Optional[str]:
        """
        抓取并保存文章
        
        Args:
            url: 文章URL
            
        Returns:
            保存的文件路径，失败返回None
        """
        try:
            self.driver = self.setup_driver()
            self.driver.get(url)
            
            # 等待文章加载
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "article-root"))
            )
            
            print(f"开始处理文章：{url}")
            
            # 加载评论
            self.load_comments(self.driver)
            
            # 提取评论数据
            comments_data = self.extract_comments(self.driver)
            
            # 获取页面源码用于BeautifulSoup解析
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # 提取文章标题
            title_tag = soup.find('h1', class_='article-title') or soup.find('title')
            if not title_tag:
                print("错误：无法找到文章标题")
                return None
            
            title = title_tag.get_text().strip()
            print(f"文章标题：{title}")
            
            # 提取作者信息
            author_name, author_link = self.extract_author_info(self.driver)
            
            # 提取文章统计数据
            stats = self.extract_article_stats(self.driver)
            
            # 提取额外元数据
            metadata = self.extract_additional_metadata(self.driver)
            
            # 提取文章内容
            article_container = soup.find(id='article-root')
            if not article_container:
                print("错误：无法找到文章内容")
                return None
            
            # Remove decorative code block elements
            for header in article_container.find_all("div", class_="code-block-extension-header"):
                header.decompose()

            # Move code from <code> to <pre> to avoid extra newlines
            for pre in article_container.find_all('pre'):
                if pre.code:
                    pre.string = pre.code.get_text().strip()
            
            markdown_content = html_to_markdown.markdownify(str(article_container))
            
            # 准备文章数据
            article_data = {
                'title': title,
                'url': url,
                'author_name': author_name,
                'author_link': author_link,
                'content': markdown_content,
                'comments_data': comments_data,
                **stats,
                **metadata
            }
            
            # 生成Markdown
            final_markdown = self.generate_markdown(article_data)
            
            # 保存文件
            safe_filename = re.sub(r'[\/*?"<>|]', "", title)
            safe_filename = safe_filename.replace(' ', '_') + ".md"
            save_path = os.path.expanduser(f"~/{safe_filename}")
            
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(final_markdown)
            
            print(f"✅ 文章已保存到：{save_path}")
            return save_path
            
        except Exception as e:
            print(f"❌ 处理文章时出错：{e}")
            return None
        
        finally:
            if self.driver:
                self.driver.quit()


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法：python juejin_scraper_final.py <URL1> [URL2] ...")
        print("示例：python juejin_scraper_final.py https://juejin.cn/post/7511582195447824438")
        sys.exit(1)
    
    scraper = JuejinScraper(headless=True, max_comments=10, max_replies=5)
    
    urls = sys.argv[1:]
    success_count = 0
    
    print(f"📚 开始处理 {len(urls)} 篇文章...")
    print("=" * 50)
    
    for i, url in enumerate(urls, 1):
        print(f"\n🔄 [{i}/{len(urls)}] 处理文章...")
        result = scraper.save_article(url)
        
        if result:
            success_count += 1
            print(f"✅ 第 {i} 篇文章处理完成")
        else:
            print(f"❌ 第 {i} 篇文章处理失败")
        
        print("-" * 30)
    
    print(f"\n🎉 处理完成！成功：{success_count}/{len(urls)} 篇文章")


if __name__ == "__main__":
    main() 