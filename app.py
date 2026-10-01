현재 화면에는 '우리 아파트 실거래가 비교 조회'라는 기본 제목과 함께 필터링되지 않은 은평구 전체 실거래가 147건이 그대로 노출되어 있습니다.   요청하신 대로 제목을 변경하고, 처음 접속했을 때 별도로 버튼을 누르지 않아도 북한산힐스테이트7차의 59㎡(소수점 무시) 데이터가 즉시 화면에 뜨도록 코드를 개선했습니다.이전과 동일하게 app.py의 내용을 모두 지우고 아래 코드로 덮어씌운 뒤 깃허브에 저장(Commit changes)해 주세요.Pythonimport streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET

# 웹 앱 페이지 기본 설정
st.set_page_config(page_title="아파트 실거래가 비교", layout="wide")

# 1. 요청하신 맞춤형 제목으로 변경
st.title("🏢 북힐7차와 다른 아파트 비교, 자산증식 합시다~혜주쓰")

# 2. 사이드바 기본 검색 조건 세팅
st.sidebar.header("검색 조건 설정")
lawd_cd = st.sidebar.text_input("지역코드 5자리", "11380")
deal_ymd = st.sidebar.text_input("계약월 (예: 202609)", "202609")

# 3. 처음 화면에 바로 띄우기 위해 아파트명과 면적의 기본값을 미리 채워둠
target_apt = st.sidebar.text_input("찾고 싶은 아파트 이름 (선택)", "북한산힐스테이트7차")
target_area = st.sidebar.text_input("전용면적(㎡) 앞자리 (예: 59)", "59")

# 버튼 없이 조건이 바뀔 때마다 즉시 데이터를 불러오도록 구조를 변경했습니다.
url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"

params = {
    'serviceKey': '014e8e30437cc041035a920222ccefa9300b972ca4da6fe54529c27c14cea8b2',
    'pageNo': '1',
    'numOfRows': '1000', 
    'LAWD_CD': lawd_cd,
    'DEAL_YMD': deal_ymd
}

with st.spinner('데이터를 불러오는 중입니다...'):
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        if items:
            data = []
            for item in items:
                apt_name = item.find('aptNm').text if item.find('aptNm') is not None else ''
                price = item.find('dealAmount').text if item.find('dealAmount') is not None else ''
                area = item.find('excluUseAr').text if item.find('excluUseAr') is not None else ''
                floor = item.find('floor').text if item.find('floor') is not None else ''
                day = item.find('dealDay').text if item.find('dealDay') is not None else ''
                
                data.append({
                    '아파트명': apt_name.strip(),
                    '거래금액(만원)': price.strip(),
                    '전용면적(㎡)': area,
                    '층': floor,
                    '거래일': f"{day}일"
                })
            
            df = pd.DataFrame(data)
            
            # 4. 전용면적 필터링: 면적 데이터(예: 59.981)를 '.' 기준으로 잘라 앞자리만 비교
            if target_area:
                df = df[df['전용면적(㎡)'].apply(lambda x: str(x).split('.')[0] == target_area.strip())]

            # 5. 아파트 이름 필터링 및 결과 출력
            if target_apt:
                filtered_df = df[df['아파트명'].str.contains(target_apt, na=False)]
                if not filtered_df.empty:
                    st.success(f"🔍 '{target_apt}' (전용면적 {target_area}㎡대) 검색 결과: 총 {len(filtered_df)}건")
                    st.dataframe(filtered_df, use_container_width=True)
                else:
                    st.warning(f"조건과 일치하는 거래 내역이 없습니다.")
            else:
                st.success(f"해당 지역 전용면적 {target_area}㎡대 전체 거래 내역: 총 {len(df)}건")
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("해당 조건에 맞는 거래 데이터가 없습니다.")
    else:
        st.error(f"API 호출 실패 (HTTP 상태 코드: {response.status_code})")
