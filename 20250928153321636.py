import requests
from bs4 import BeautifulSoup
import html_to_markdown
import sys
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Dict, Tuple

def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def extract_author_info(driver: webdriver.Chrome) -> Tuple[str, str]:
    """提取作者信息"""
    print("提取作者信息...")
    try:
        # Wait for the author info block to be present
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".author-info-block .author-name a"))
        )
        author_link_element = driver.find_element(By.CSS_SELECTOR, ".author-info-block .author-name a")
        author_name_element = author_link_element.find_element(By.CSS_SELECTOR, ".name")
        
        author_name = author_name_element.get_attribute('textContent').strip()
        author_link = author_link_element.get_attribute("href")

        if author_name and author_link:
            if author_link.startswith('/'):
                author_link = "https://juejin.cn" + author_link
            print(f"找到作者：{author_name}")
            return author_name, author_link

    except Exception as e:
        print(f"提取作者信息失败：{e}")
    
    return "未知作者", ""

def extract_article_stats(driver: webdriver.Chrome) -> Dict[str, int]:
    """提取文章统计数据（点赞、评论、收藏）"""
    print("提取文章统计数据...")
    stats = {'likes': 0, 'comments': 0, 'collects': 0}
    try:
        panel_buttons = driver.find_elements(By.CSS_SELECTOR, ".panel-btn.with-badge")
        for button in panel_buttons:
            try:
                badge_value = button.get_attribute("badge")
                if not badge_value:
                    continue
                svg_element = button.find_element(By.CSS_SELECTOR, "svg")
                svg_class = svg_element.get_attribute("class")
                if "icon-zan" in svg_class:
                    stats['likes'] = int(badge_value)
                elif "icon-comment" in svg_class:
                    stats['comments'] = int(badge_value)
                elif "icon-collect" in svg_class:
                    stats['collects'] = int(badge_value)
            except Exception as e:
                print(f"处理统计按钮时出错：{e}")
                continue
    except Exception as e:
        print(f"提取统计数据失败：{e}")
    return stats

def extract_additional_metadata(driver: webdriver.Chrome) -> Dict[str, str]:
    """提取额外的元数据"""
    metadata = {}
    print("提取额外元数据...")
    try:
        time_element = driver.find_element(By.CSS_SELECTOR, "time.time")
        metadata['publish_time'] = time_element.text.strip()
    except:
        metadata['publish_time'] = "未知时间"
    try:
        page_text = driver.execute_script("return document.body.innerText;")
        read_match = re.search(r'阅读(\\d+分钟)', page_text)
        metadata['read_time'] = read_match.group(1) if read_match else "未知"
    except:
        metadata['read_time'] = "未知"
    
    metadata['column'] = "无专栏"
    return metadata

def save_juejin_article_as_md(url, driver):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "article-root"))
        )
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        title_tag = soup.find('h1', class_='article-title') or soup.find('title')
        if not title_tag:
            print("Error: Could not find the article title.", file=sys.stderr)
            return
        title = title_tag.get_text().strip()
        
        safe_filename = re.sub(r'[\\/*?"<>|]', "", title).replace(' ', '_') + ".md"

        # Extract metadata
        author_name, author_link = extract_author_info(driver)
        stats = extract_article_stats(driver)
        metadata = extract_additional_metadata(driver)

        article_container = soup.find(id='article-root')
        if not article_container:
            print("Error: Could not find article content with id='article-root'.", file=sys.stderr)
            return

        for header in article_container.find_all("div", class_="code-block-extension-header"):
            header.decompose()
        for pre in article_container.find_all('pre'):
            if pre.code:
                pre.string = pre.code.get_text().strip()

        markdown_content = html_to_markdown.markdownify(str(article_container))

        # Generate new markdown with header
        md_parts = []
        md_parts.append(f"# {title}")
        if author_link:
            md_parts.append(f"**作者：** [{author_name}]({author_link})")
        else:
            md_parts.append(f"**作者：** {author_name}")
        
        table_lines = []
        table_lines.append("## 📊 文章信息")
        table_lines.append("| 项目 | 内容 |")
        table_lines.append("|------|------|")
        table_lines.append(f"| 发表时间 | {metadata.get('publish_time', '未知')} |")
        table_lines.append(f"| 点赞数 | {stats.get('likes', 0)} |")
        table_lines.append(f"| 评论数 | {stats.get('comments', 0)} |")
        table_lines.append(f"| 收藏数 | {stats.get('collects', 0)} |")
        table_lines.append(f"| 阅读时长 | {metadata.get('read_time', '未知')} |")
        table_lines.append(f"| 专栏名称 | {metadata.get('column', '无专栏')} |")
        table_lines.append(f"| 原文链接 | [{title}]({url}) |")
        
        md_parts.append("\n".join(table_lines))
        
        md_parts.append("---")
        md_parts.append("## 📝 文章内容")
        md_parts.append(markdown_content)
        
        final_markdown = "\n\n".join(md_parts)

        save_path = os.path.expanduser(f"~/{safe_filename}")
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(final_markdown)
        
        print(f"Successfully saved article to: {save_path}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        driver = get_driver()
        for url in sys.argv[1:]:
            print(f"Processing URL: {url}")
            save_juejin_article_as_md(url, driver)
            print("-" * 20)
        driver.quit()
    else:
        print("Usage: python juejin_to_local_md.py <URL1> <URL2> ...", file=sys.stderr)