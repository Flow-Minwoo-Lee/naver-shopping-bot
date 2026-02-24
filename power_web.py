import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random

# 페이지 설정
st.set_page_config(page_title="네이버 쇼핑 크롤러", page_icon="🛍️")
st.title("🛡️ 반자동 우회형 네이버 쇼핑 크롤러 #gemini")
st.info("💡 인증창(CAPTCHA)이 뜨면 브라우저에서 직접 해결해 주세요. 프로그램이 최대 1분간 기다립니다.")

keyword = st.text_input("검색어를 입력하세요", "노트북")

if st.button("데이터 수집 시작!"):
    with st.spinner('브라우저 실행 중...'):
        options = Options()
        # 자동화 감지 회피를 위한 필수 설정
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            # 1. 네이버 메인 접속 및 검색 (사람처럼 행동)
            driver.get("https://www.naver.com")
            time.sleep(random.uniform(1.5, 2.5))
            
            search_box = driver.find_element(By.ID, "query")
            for char in keyword:
                search_box.send_keys(char)
                time.sleep(random.uniform(0.1, 0.2))
            search_box.send_keys(Keys.ENTER)
            time.sleep(2)

            # 2. 쇼핑 페이지로 이동
            driver.get(f"https://search.shopping.naver.com/search/all?query={keyword}")

            # 3. [핵심] 인내심 로직: 상품 목록이 나타날 때까지 기다림
            # 사용자가 인증창을 푸는 시간을 벌어줍니다 (최대 60초)
            with st.status("상품 목록 로딩 대기 중... (인증창이 뜨면 풀어주세요!)") as status:
                try:
                    # 상품 아이템(_item__)이 화면에 보일 때까지 대기
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[class*="_item__"]'))
                    )
                    status.update(label="데이터 포착 성공!", state="complete")
                except:
                    st.error("60초 동안 상품 목록을 찾지 못했습니다. 인증을 실패했거나 페이지 구조가 변경되었을 수 있습니다.")
                    driver.quit()
                    st.stop()

            # 4. 데이터 로딩을 위해 스크롤
            driver.execute_script("window.scrollTo(0, 1500);")
            time.sleep(2)

            # 5. 데이터 추출 (사용자 제공 HTML 구조 반영)
            items = driver.find_elements(By.CSS_SELECTOR, '[class*="_item__"]')
            results = []
            
            for item in items:
                try:
                    # 클래스명에 _title__과 price_num__이 포함된 요소를 정밀 타격
                    name = item.find_element(By.CSS_SELECTOR, '[class*="_title__"]').text.strip()
                    price = item.find_element(By.CSS_SELECTOR, '[class*="price_num__"]').text.strip()
                    
                    if name and price:
                        results.append({"상품명": name, "가격": price})
                except:
                    continue

            # 6. 결과 출력
            df = pd.DataFrame(results).drop_duplicates()
            
            if not df.empty:
                st.success(f"🎉 총 {len(df)}개의 상품 데이터를 수집했습니다!")
                st.dataframe(df, use_container_width=True)
                
                # CSV 다운로드 버튼
                csv = df.to_csv(index=False).encode('utf-16')
                st.download_button("📥 엑셀(CSV) 파일 다운로드", csv, f"naver_{keyword}.csv", "text/csv")
            else:
                st.warning("화면에는 상품이 보이지만 데이터를 추출하지 못했습니다. 선택자(Selector) 점검이 필요합니다.")

        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")
        
        # 테스트를 위해 브라우저는 닫지 않고 유지합니다.