import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET

# 웹 앱 페이지 기본 설정
st.set_page_config(page_title="은평구 아파트 실거래가", layout="wide")
st.title("🏢 우리 아파트 실거래가 비교 조회")

# 1. 왼쪽 사이드바 검색 조건 만들기
st.sidebar.header("검색 조건 설정")
# 은평구 코드(11380)를 기본값으로 세팅
lawd_cd = st.sidebar.text_input("지역코드 5자리", "11380")
deal_ymd = st.sidebar.text_input("계약월 (예: 202609)", "202609")
target_apt = st.sidebar.text_input("찾고 싶은 아파트 이름 (선택)", "")

# 2. 조회 버튼을 눌렀을 때 실행될 로직
if st.sidebar.button("실거래가 조회하기"):
    # 기술명세서 기준 최신 API 주소
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
    
    params = {
        'serviceKey': '014e8e30437cc041035a920222ccefa9300b972ca4da6fe54529c27c14cea8b2',
        'pageNo': '1',
        'numOfRows': '1000', 
        'LAWD_CD': lawd_cd,
        'DEAL_YMD': deal_ymd
    }

    # 로딩 애니메이션 표시
    with st.spinner('공공데이터를 불러오는 중입니다...'):
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            
            if items:
                data = []
                for item in items:
                    # 기술명세서 응답 메시지에 맞춘 영문 태그 추출
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
                
                # 3. 특정 아파트 필터링 (결과 출력)
                if target_apt:
                    filtered_df = df[df['아파트명'].str.contains(target_apt, na=False)]
                    if not filtered_df.empty:
                        st.success(f"🔍 '{target_apt}' 검색 결과: 총 {len(filtered_df)}건")
                        st.dataframe(filtered_df, use_container_width=True)
                    else:
                        st.warning(f"해당 월에 '{target_apt}' 아파트의 거래 내역이 없습니다.")
                else:
                    st.success(f"은평구 전체 거래 내역: 총 {len(df)}건")
                    st.dataframe(df, use_container_width=True)
            else:
                st.warning("해당 조건에 맞는 거래 데이터가 없습니다.")
        else:
            st.error(f"API 호출 실패 (HTTP 상태 코드: {response.status_code})")
