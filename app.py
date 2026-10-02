import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. 페이지 기본 설정 및 제목 변경
st.set_page_config(page_title="아파트 실거래가 비교", layout="wide")
st.title("🏢 북힐7차와 다른 아파트 비교, 자산증식 합시다~혜주쓰")

# 2. 날짜 기본값 계산 (오늘 기준)
today = datetime.today()
current_year = today.year # 올해 연도 (예: 2026)
last_month = today - relativedelta(months=1)
default_month_str = last_month.strftime("%Y%m")

# 드롭다운용 최근 3년(36개월) 월 리스트 생성
month_list = [(today - relativedelta(months=i)).strftime("%Y%m") for i in range(36)]

# 3. 사이드바 UI 설정
st.sidebar.header("검색 조건 설정")
lawd_cd = st.sidebar.text_input("지역코드 5자리", "11380")

st.sidebar.subheader("조회 기간")
col1, col2 = st.sidebar.columns(2)
with col1:
    # index를 활용해 기본값을 전달로 지정
    start_month = st.selectbox("시작 월", month_list[::-1], index=month_list[::-1].index(default_month_str))
with col2:
    end_month = st.selectbox("종료 월", month_list[::-1], index=month_list[::-1].index(default_month_str))

target_area = st.sidebar.text_input("전용면적(㎡) 앞자리 (예: 59)", "59")

# 비교할 아파트 목록 세팅
default_apts = ["북한산힐스테이트7차", "북한산현대힐스테이트3차", "래미안베라힐즈", "불광롯데캐슬"]
selected_apts = st.sidebar.multiselect("비교 대상 아파트", default_apts, default=default_apts)

if start_month > end_month:
    st.sidebar.error("시작 월이 종료 월보다 늦을 수 없습니다.")
    st.stop()

# 4. 데이터 조회 (시작월~종료월)
start_dt = pd.to_datetime(start_month, format='%Y%m')
end_dt = pd.to_datetime(end_month, format='%Y%m')
months_to_fetch = pd.date_range(start=start_dt, end=end_dt, freq='MS').strftime("%Y%m").tolist()

url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
all_data = []

# API는 한 번에 한 달치만 조회 가능하므로 월별로 반복 호출
with st.spinner('여러 달의 데이터를 불러오는 중입니다... (조금만 기다려주세요)'):
    for ymd in months_to_fetch:
        params = {
            'serviceKey': '014e8e30437cc041035a920222ccefa9300b972ca4da6fe54529c27c14cea8b2',
            'pageNo': '1',
            'numOfRows': '1000', 
            'LAWD_CD': lawd_cd,
            'DEAL_YMD': ymd
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            for item in items:
                apt_name = item.find('aptNm').text.strip() if item.find('aptNm') is not None else ''
                
                # 선택된 아파트(4종) 중 하나인지 확인
                if any(apt in apt_name for apt in selected_apts):
                    area = item.find('excluUseAr').text if item.find('excluUseAr') is not None else '0'
                    
                    # 면적 필터링 (59㎡)
                    if str(area).split('.')[0] == target_area.strip():
                        price_str = item.find('dealAmount').text.strip() if item.find('dealAmount') is not None else '0'
                        floor = item.find('floor').text if item.find('floor') is not None else '0'
                        day = item.find('dealDay').text.zfill(2) if item.find('dealDay') is not None else ''
                        month = item.find('dealMonth').text.zfill(2) if item.find('dealMonth') is not None else ''
                        year = item.find('dealYear').text if item.find('dealYear') is not None else ''
                        
                        price_num = int(price_str.replace(',', ''))
                        
                        all_data.append({
                            '계약월': f"{year}-{month}",
                            '거래일': f"{day}일",
                            '아파트명': apt_name,
                            '전용면적(㎡)': area,
                            '층': floor,
                            '거래금액(만원)': price_num
                        })

    # 5. 수집된 데이터 가공 및 표(UI) 출력
    if all_data:
        df = pd.DataFrame(all_data)
        
        # 🌟 [수정된 부분] 8월을 기준으로 문자열 생성 (예: '2026-08')
        august_str = f"{current_year}-08"
        
        # 🌟 [수정된 부분] 북힐7차 데이터 중 '8월 이후' 데이터만 추출
        our_apt_df = df[
            (df['아파트명'].str.contains('북한산힐스테이트7차')) & 
            (df['계약월'] >= august_str)
        ]
        
        if not our_apt_df.empty:
            # 🌟 [수정된 부분] mean()(평균) 대신 max()(최고가)를 사용합니다!
            our_base_price = our_apt_df['거래금액(만원)'].max()
            
            # 차액 계산 (비교 아파트 가격 - 우리집 8월 이후 최고가)
            df['우리집 최고가대비 차액'] = df['거래금액(만원)'] - our_base_price
            df['우리집 최고가대비 차액'] = df['우리집 최고가대비 차액'].apply(
                lambda x: f"🔺 +{int(x):,}만원" if x > 0 else (f"🔻 {int(x):,}만원" if x < 0 else "-")
            )
            
            st.info(f"💡 기준가 설정 완료: **북한산힐스테이트7차 {target_area}㎡**의 {current_year}년 8월~현재 **최고 실거래가는 {int(our_base_price):,}만원**입니다.")
        else:
            # 8월 이후 거래가 없거나, 검색 기간에 8월 이후가 포함되지 않은 경우
            df['우리집 최고가대비 차액'] = "최고가 산정불가"
            st.warning(f"⚠️ 검색하신 기간 내에 {current_year}년 8월 이후 '북한산힐스테이트7차' 거래가 없어 기준가(최고가)를 계산할 수 없습니다. 사이드바에서 조회 기간을 8월 이후로 설정해주세요!")

        # 가격 컬럼 보기 좋게 천 단위 콤마 추가
        df['거래금액(만원)'] = df['거래금액(만원)'].apply(lambda x: f"{x:,}")
        
        # 최신 거래일자 순으로 정렬
        df = df.sort_values(by=['계약월', '거래일'], ascending=[False, False])
        
        st.success(f"조회 완료: 선택한 아파트 총 {len(df)}건 거래 (전용 {target_area}㎡ 기준)")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.warning("선택한 기간 내 조건에 맞는 거래 데이터가 없습니다.")
