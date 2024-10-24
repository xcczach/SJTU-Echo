from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)
import time

# 配置 Chrome 浏览器选项（可选）
chrome_options = Options()
chrome_options.add_argument("--headless")  # 无头模式，不显示浏览器界面

# 初始化 WebDriver
driver = webdriver.Chrome(options=chrome_options)

# 访问目标网页
original_url = "https://www.sjtu.edu.cn/tg/index.html"  # 替换为您的目标 URL
driver.get(original_url)

# 等待页面加载完成
time.sleep(2)

# 获取页面标题，便于返回时验证
original_title = driver.title

# 记录已访问的 URL（避免重复）
visited_urls = set()

# 查找所有可能的可点击元素
clickable_selectors = [
    "a[href]",  # 所有链接
    "button",  # 按钮
    "input[type='button']",
    "input[type='submit']",
    "[role='button']",  # 具有按钮角色的元素
    "[tabindex]",  # 具有 tabindex 属性的元素，可能可点击
    "div",
    "span",
    "*[onclick]",  # 包含 onclick 属性的元素
]

# 将所有选择器组合成一个
all_clickable_selector = ", ".join(clickable_selectors)

# 获取所有可能的可点击元素
elements = driver.find_elements(By.CSS_SELECTOR, all_clickable_selector)

print(f"找到 {len(elements)} 个可能的可点击元素。")

for index, element in enumerate(elements):
    try:
        # 获取元素的描述信息，便于调试
        element_info = element.tag_name
        print(f"\n正在尝试点击第 {index + 1} 个元素：{element_info}")

        # 在点击之前，获取当前的窗口句柄和 URL
        current_window = driver.current_window_handle
        current_url = driver.current_url

        # 点击元素
        element.click()

        # 等待页面可能的跳转
        time.sleep(2)

        # 获取所有窗口句柄
        all_windows = driver.window_handles

        if len(all_windows) > 1:
            # 如果打开了新的窗口或标签页，切换到新窗口
            for window in all_windows:
                if window != current_window:
                    driver.switch_to.window(window)
                    break
            new_url = driver.current_url
            print(f"点击后打开了新窗口，目标 URL：{new_url}")
            visited_urls.add(new_url)
            # 关闭新窗口，返回原窗口
            driver.close()
            driver.switch_to.window(current_window)
        else:
            new_url = driver.current_url
            if new_url != current_url:
                print(f"发生导航，目标 URL：{new_url}")
                visited_urls.add(new_url)
                # 返回原页面
                driver.back()
                time.sleep(2)
                # 验证是否成功返回
                if driver.title != original_title:
                    print("无法返回原页面，停止执行。")
                    break
            else:
                print("未发生导航。")
    except (ElementClickInterceptedException, ElementNotInteractableException) as e:
        print(f"元素不可点击：{e}")
        continue
    except StaleElementReferenceException as e:
        print(f"元素已失效：{e}")
        continue
    except Exception as e:
        print(f"点击元素时发生错误：{e}")
        continue

# 输出所有收集到的目标 URL
print("\n收集到的目标 URL：")
for url in visited_urls:
    print(url)

# 关闭浏览器
driver.quit()
