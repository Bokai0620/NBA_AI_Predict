from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import urllib3
import time

#==============================封裝一個建立 driver 的函式，方便重啟=========================================================
def create_driver():
    service = Service("D:/AI_prediction/Selenium/chromedriver-win64/chromedriver.exe") # 指定 chromedriver.exe 的路徑
    chrome_options = Options()
    chrome_options.page_load_strategy = 'normal'
    d = webdriver.Chrome(service=service, options=chrome_options)
    d.set_page_load_timeout(180) # 最長等候 180 秒
    return d 
#==============================封裝一個建立 driver 的函式，方便重啟=========================================================

#=====================數值轉換函數======================
def safe_number(val):
    """
    安全將字串轉成數字
    - 空字串或 '-' 會回傳 0.0
    - 小數點開頭 '.xxx' 會轉成 0.xxx
    - 百分比欄位可選自動除以 100
    - 如果是整數，回傳 int
    """
    val = val.strip().replace('%', '')  # 去掉空白和 %
    
    if val == '' or val == '-':
        return 0.0
    
    if val.startswith('.'):
        val = '0' + val
    
    try:
        num = float(val)

        # 如果數字是整數，回傳 int
        if num.is_integer():
            return int(num)
        return num
    except:
        return 0.0
#=======================================================

#========================進入url開始檢查使否發生例外================================
def try_get_with_retries(driver, url, max_retries=3, wait_between=3):
    """嘗試用 driver.get 取得 URL，發生例外時重試並視情況重啟 driver"""
    tries = 0
    while tries < max_retries:
        tries += 1
        try:
            driver.get(url)
            return True, driver  # 成功
        except TimeoutException as te:
            print(f"[TimeoutException] 第{tries}次載入 {url} 超時: {te}")
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
        except WebDriverException as we:
            # WebDriverException 常見於 chromedriver/瀏覽器死掉或連線中斷
            print(f"[WebDriverException] 第{tries}次載入 {url} 發生 WebDriverException: {we}")
            try:
                driver.quit()
            except Exception:
                pass
            time.sleep(1)
            # 重啟 driver（回傳新的 driver 物件）
            driver = create_driver()
        except urllib3.exceptions.ReadTimeoutError as re:
            # 這是你在 traceback 中看到的底層例外
            print(f"[urllib3 ReadTimeoutError] 第{tries}次載入 {url}: {re}")
            try:
                driver.execute_script("window.stop();")
            except Exception:
                pass
        except Exception as e:
            # 捕捉其他不可預期的錯誤，記錄後嘗試重啟 driver
            print(f"[Exception] 第{tries}次載入 {url} 發生例外: {type(e).__name__}: {e}")
            try:
                driver.quit()
            except Exception:
                pass
            driver = create_driver()
        # 等待再重試
        time.sleep(wait_between)
    # 若所有重試都失敗則回傳 False 與目前 driver（可能是新建的）
    return False, driver
#========================進入url開始檢查使否發生例外================================

#=====================進入網站 & 變數宣告=====================================================
# 如果你原本已建立 driver，改成用這個
driver = create_driver()

# 開啟網站
driver.get("https://www.basketball-reference.com/boxscores/?month=1&day=1&year=2021")

count = 0 #網頁計數
all_teams_data = []  # 存所有隊伍的資料
year_select_text = "0" # 先宣告年(例: 2021)
month_select_text = "0" # 先宣告月(例: January)
day_select_text = "0" # 先宣告日(例: 1)
#=====================進入網站 & 變數宣告=====================================================
    
    
    
#選擇期間內的資料
while True:
    #找出當前年份
    year_select_elem = driver.find_element(By.ID, "year") #抓取下拉式選單格子
    year_select = Select(year_select_elem) #改成Select的物件這樣才能利用first_selected_option.text此方法
    year_select_text = year_select.first_selected_option.text
    print(year_select_text) #string型態
    # 立即檢查；如果已經到 2025，就不要處理 2025，直接結束
    if year_select_text == "2025":
        print("已到 2025，結束爬取。")
        break

    #找出當前月份
    month_select_elem = driver.find_element(By.ID, "month") #抓取下拉式選單格子
    month_select = Select(month_select_elem) #改成Select的物件這樣才能利用first_selected_option.text此方法
    month_select_text = month_select.first_selected_option.text
    print(month_select_text) #string型態

    #找出當前日期
    day_select_elem = driver.find_element(By.ID, "day") #抓取下拉式選單格子
    day_select = Select(day_select_elem) #改成Select的物件這樣才能利用first_selected_option.text此方法
    day_select_text = day_select.first_selected_option.text
    print(day_select_text) #string型態
    
    count += 1
    # 抓取所有 Box Score 連結
    box_score_elements = driver.find_elements(By.LINK_TEXT, "Box Score")

    # if box_score_elements:
    box_score_links = []
    for elem in box_score_elements:
        link = elem.get_attribute("href")
        box_score_links.append(link)

    #抓取下一頁的按鈕
    next_link_elem = driver.find_element(By.CLASS_NAME, "next") 
    
    #取出下一頁的連結
    next_link = next_link_elem.get_attribute("href") 

    print(f"第{count}頁: ")
    
    # 依序進入每個Box Score連結
    max_retries = 3

    for link in box_score_links:
        ok, driver = try_get_with_retries(driver, link, max_retries=3, wait_between=4)
        if not ok:
            print(f"多次重試仍無法載入 {link}，已跳過並記錄。")
            # 可把失敗的 link 寫入檔案或清單方便後續檢查
            with open("failed_links.txt", "a", encoding="utf-8") as f:
                f.write(link + "\n")
            continue

        # 成功載入後再做等待 scorebox 的動作
        try:
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, "scorebox"))
            )
        except TimeoutException:
            print(f"{link} 載入後仍找不到 scorebox，跳過")
            continue
        
        
        # 抓 Basic_Box_Score 的 table
        try:
            # 抓 Basic_Box_Score 的 table（可能是兩個 table）
            tables = driver.find_elements(By.XPATH, '//table[contains(@id, "game-basic")]')
            if not tables:
                print(f"{link} 找不到 game-basic table，跳過此場比賽")
                continue
        
            # 抓 scorebox（理論上已等過，但再保險處理）
            try:
                scorebox = driver.find_element(By.CLASS_NAME, "scorebox")
            except NoSuchElementException:
                print(f"{link} 無法找到 scorebox（NoSuchElement），跳過此場比賽")
                continue

            # 抓兩隊的分數（檢查長度）
            scores = scorebox.find_elements(By.XPATH, './/div[@class="scores"]/div[@class="score"]')
            if len(scores) < 2:
                print(f"{link} scores 長度 < 2，內容: {[s.text for s in scores]}，跳過")
                continue
        
            # 嘗試轉 int（保護 ValueError）
            try:
                score1 = int(scores[0].text.strip())
                score2 = int(scores[1].text.strip())
            except ValueError:
                print(f"{link} score 轉 int 失敗，score texts: '{scores[0].text}', '{scores[1].text}'，跳過")
                continue
            
            # 比較2隊的分數看誰輸誰贏
            game_dict_team1 = {} #第1隊的結果字典
            game_dict_team2 = {} #第2隊的結果字典
            if score1 > score2:
                game_dict_team1['result'] = 1  # 贏
                game_dict_team2['result'] = 0  # 輸
            else:
                game_dict_team1['result'] = 0
                game_dict_team2['result'] = 1            
            
            team_count = 0
            
            # 逐隊處理 tables
            for table in tables:
                team_count += 1
                try:
                    team_totals_row = table.find_element(By.XPATH, './/tr[th[text()="Team Totals"]]')
                except NoSuchElementException:
                    print(f"{link} 第{team_count}隊找不到 Team Totals 列，跳過該隊")
                    continue

                team_totals = team_totals_row.find_elements(By.CSS_SELECTOR,
                    'td[data-stat]:not([data-stat="mp"]):not([data-stat="game_score"]):not([data-stat="plus_minus"]):not([data-stat="pts"])'
                )

                if not team_totals:
                    print(f"{link} 第{team_count}隊 Team Totals 沒有 td[data-stat]，跳過該隊")
                    continue
                    
                print(f"第{team_count}隊資訊正在加入team_dict字典中...\n")
                team_dict = {}
                # 把每隊的資訊加入 team_dict（safe_number 已處理非數值）
                for team_info in team_totals:
                    stat_name = team_info.get_attribute("data-stat")
                    stat_value = team_info.text.strip()
                    stat_value = safe_number(stat_value)
                    team_dict[stat_name] = stat_value

                # 安全計算 2 分球（處理 KeyError & 分母為 0）
                try:
                    # 若缺任何欄位則先設為 0
                    fg = team_dict.get("fg", 0)
                    fg3 = team_dict.get("fg3", 0)
                    fga = team_dict.get("fga", 0)
                    fg3a = team_dict.get("fg3a", 0)

                    fg2 = fg - fg3
                    fga2 = fga - fg3a

                    team_dict["fg2"] = fg2
                    team_dict["fga2"] = fga2

                    if fga2 and fga2 != 0:
                        team_dict["fg2_pct"] = fg2 / fga2
                    else:
                        team_dict["fg2_pct"] = 0.0
                except Exception as e:
                    # 捕捉任何計算意外，並預設值
                    print(f"{link} 第{team_count}隊 在計算 2 分球時發生錯誤: {e}; 設預設值並繼續")
                    team_dict.setdefault("fg2", 0)
                    team_dict.setdefault("fga2", 0)
                    team_dict.setdefault("fg2_pct", 0.0)

                # 把輸贏加入 team_dict
                if team_count == 1:
                    team_dict["result"] = game_dict_team1['result']
                elif team_count == 2:
                    team_dict["result"] = game_dict_team2['result']

                all_teams_data.append(team_dict)

        except Exception as e:
            # 最後的保護：任何不可預期錯誤記錄後跳過這場比賽
            print(f"{link} 在解析比賽資料時發生不可預期錯誤: {type(e).__name__}: {e}")
            # 可以選擇把 link 寫入失敗檔案
            with open("failed_parsing_links.txt", "a", encoding="utf-8") as f:
                f.write(f"{link} -> {type(e).__name__}: {e}\n")
            continue       
            
                   
    # 抓下一頁（用 try_get_with_retries 包裝）
    ok, driver = try_get_with_retries(driver, next_link, max_retries=3, wait_between=4)
    if not ok:
        print(f"多次重試仍無法載入下一頁 {next_link}，結束或跳過迴圈。")
        # 你可以選擇 break 結束整個 while 或 continue 繼續下一個 year/month/day loop
        # 我這裡示範跳出主迴圈結束爬取
        break
    # 如果 ok == True，就會繼續下一輪 while（已經把 driver 更新回來）
        
# print(all_teams_data)     

print("正在轉換成Data Frame...\n")
# 轉換成Data Frame
df = pd.DataFrame(all_teams_data) 
print(df.head())    

print("正在存成CSV檔...")
# 存成 CSV
df.to_csv("D:/AI_prediction/python_program/program1/new_all_teams_data.csv", index=False, encoding="utf-8-sig")
    
# 關閉瀏覽器
driver.quit()
