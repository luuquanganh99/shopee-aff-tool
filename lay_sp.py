from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json, time, re

# ── ĐƯỜNG DẪN CHROME PROFILE CỦA BẠN ────────────────
CHROME_USER_DATA = r"C:\Users\Admin\AppData\Local\Google\Chrome\User Data"
CHROME_PROFILE = "Default"

def lay_du_lieu():
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={CHROME_USER_DATA}")
    options.add_argument(f"--profile-directory={CHROME_PROFILE}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    wait = WebDriverWait(driver, 15)

    try:
        print("🌐 Đang mở trang Hoa hồng Sản phẩm...")
        driver.get("https://affiliate.shopee.vn/product/item_list")
        time.sleep(5)

        # Kiểm tra đã vào được chưa
        if "login" in driver.current_url or "verify" in driver.current_url:
            print("⚠ Cần đăng nhập! Hãy đăng nhập trên Chrome đang mở...")
            input("   >> Đăng nhập xong nhấn Enter: ")
            driver.get("https://affiliate.shopee.vn/product/item_list")
            time.sleep(5)

        print("✅ Vào được trang sản phẩm!\n")

        products = []
        MAX_SP = 9

        # Lấy tất cả card sản phẩm
        print("🔍 Đang tìm sản phẩm...")
        time.sleep(3)

        # Chụp HTML để debug
        cards = driver.find_elements(By.CSS_SELECTOR,
            "[class*='product'], [class*='item'], [class*='card']")
        print(f"   Tìm thấy {len(cards)} elements")

        # Thử lấy bằng JS
        sp_data = driver.execute_script("""
            let results = [];
            
            // Tìm tất cả card có chứa nút "Lấy link"
            let buttons = document.querySelectorAll('button');
            let layLinkBtns = [];
            for(let btn of buttons) {
                if(btn.innerText.includes('Lấy link') || btn.innerText.includes('Get link')) {
                    layLinkBtns.push(btn);
                }
            }
            
            for(let btn of layLinkBtns) {
                // Tìm card cha
                let card = btn.closest('[class*="product"], [class*="item"], [class*="card"], li, article');
                if(!card) card = btn.parentElement?.parentElement?.parentElement;
                if(!card) continue;
                
                // Lấy thông tin
                let ten = card.querySelector('p, h3, [class*="name"], [class*="title"]')?.innerText?.trim() || '';
                let gia = '';
                let prices = card.querySelectorAll('[class*="price"]');
                if(prices.length > 0) gia = prices[0].innerText.trim().split('\\n')[0];
                
                let giam = card.querySelector('[class*="discount"], [class*="giảm"]')?.innerText || '0';
                let luot_ban = card.querySelector('[class*="sold"], [class*="lượt"]')?.innerText || '0';
                let anh = card.querySelector('img')?.src || '';
                let hoa_hong = '';
                let hh_els = card.querySelectorAll('[class*="commission"], [class*="hoa"], [class*="tỉ lệ"]');
                if(hh_els.length > 0) hoa_hong = hh_els[0].innerText;
                
                results.push({ten, gia, giam, luot_ban, anh, hoa_hong});
            }
            return results;
        """)

        print(f"   JS tìm thấy {len(sp_data)} sản phẩm có nút Lấy link")

        # Nếu JS không lấy được → chụp màn hình để debug
        if not sp_data:
            driver.save_screenshot("debug.png")
            print("   ⚠ Chụp màn hình debug.png để kiểm tra")
            
            # In HTML để xem cấu trúc
            body_html = driver.execute_script(
                "return document.body.innerHTML.substring(0, 2000)"
            )
            print("\n📄 HTML đầu trang:")
            print(body_html[:500])
            input("\nNhấn Enter để tiếp tục...")

        # Nhấn từng nút Lấy link
        btns = driver.find_elements(By.XPATH,
            "//button[contains(text(),'Lấy link') or contains(text(),'Get link')]")
        print(f"\n🔘 Tìm thấy {len(btns)} nút 'Lấy link'")

        for i, btn in enumerate(btns[:MAX_SP]):
            try:
                sp_info = sp_data[i] if i < len(sp_data) else {}

                # Scroll đến nút
                driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                time.sleep(1)

                # Nhấn nút
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(2)

                # Lấy link từ popup
                link_aff = ""
                try:
                    link_input = wait.until(EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "input[value*='shopee'], input[value*='s.shopee'], [class*='link'] input"
                    )))
                    link_aff = link_input.get_attribute("value")
                except:
                    # Thử cách khác
                    try:
                        all_inputs = driver.find_elements(By.CSS_SELECTOR, "input")
                        for inp in all_inputs:
                            val = inp.get_attribute("value") or ""
                            if "shopee" in val.lower():
                                link_aff = val
                                break
                    except:
                        pass

                # Đóng popup
                try:
                    close_btn = driver.find_element(By.CSS_SELECTOR,
                        "[class*='close'], [aria-label='Close'], [class*='modal'] button:last-child")
                    close_btn.click()
                    time.sleep(1)
                except:
                    driver.execute_script("""
                        let modals = document.querySelectorAll('[class*="modal"], [class*="popup"], [class*="dialog"]');
                        modals.forEach(m => m.remove());
                        let overlays = document.querySelectorAll('[class*="overlay"], [class*="backdrop"]');
                        overlays.forEach(o => o.remove());
                    """)
                    time.sleep(1)

                # Xử lý số
                gia_raw = re.sub(r'[^\d,.]', '', (sp_info.get('gia') or '').split('\n')[0])
                giam_raw = int(re.sub(r'[^\d]', '', sp_info.get('giam') or '0') or 0)
                luot_raw = sp_info.get('luot_ban') or '0'
                luot_num = int(re.sub(r'[^\d]', '',
                    luot_raw.replace('k', '000').replace('K', '000').replace('+', '')) or 0)

                sp = {
                    "ten": (sp_info.get('ten') or f"Sản phẩm {i+1}")[:100],
                    "gia": gia_raw or "Xem tại link",
                    "giam": giam_raw,
                    "luot_ban": luot_num,
                    "danh_gia": 5.0,
                    "hoa_hong": sp_info.get('hoa_hong', ''),
                    "anh_url": sp_info.get('anh') or "",
                    "link_goc": link_aff or "https://s.shopee.vn/4qBya6aKUi",
                    "link_aff": link_aff or "https://s.shopee.vn/4qBya6aKUi"
                }
                products.append(sp)
                print(f"   ✓ [{i+1}] {sp['ten'][:40]}...")
                print(f"       💰{sp['gia']}đ | 📉{sp['giam']}% | 🔗{'✓' if link_aff else '✗'}")

            except Exception as e:
                print(f"   ❌ Lỗi nút {i+1}: {e}")

        # Lưu file
        with open("products.json", "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Đã lưu {len(products)} sản phẩm!")
        print("👉 Chạy python main.py để đăng bài!")

    finally:
        input("\nNhấn Enter để đóng Chrome...")
        driver.quit()

if __name__ == "__main__":
    lay_du_lieu()