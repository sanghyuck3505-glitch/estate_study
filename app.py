## 아파트 실거래가 앱

import streamlit as st
import requests
import pandas as pd
import xml.etree.ElementTree as ET

st.set_page_config(page_title="우리아파트 실거래가", layout="wide")
st.title("🏢 아파트 실거래가 비교 검색기")

# 1. 왼쪽 사이드바에 검색 조건(UI) 만들기
st.sidebar.header("검색 조건 설정")
lawd_cd = st.sidebar.text_input("지역코드 5자리 (예: 11680 - 강남구)", "11680")
deal_ymd = st.sidebar.text_input("계약월 (예: 202312)", "202312")
target_apt = st.sidebar.text_input("찾고 싶은 아파트 이름 (선택)", "")

# 2. '데이터 가져오기' 버튼을 눌렀을 때 실행될 로직
if st.sidebar.button("데이터 가져오기"):
    # 국토교통부 아파트매매 실거래 상세 자료 API 주소
    url = "http://openapi.molit.go.kr/OpenAPI_ToolInstallPackage/service/rest/RTMSOBJSvc/getRTMSDataSvcAptTradeDev"
    
    # API 요청에 필요한 파라미터 세팅 (발급받은 키 적용)
    params = {
        'serviceKey': '014e8e30437cc041035a920222ccefa9300b972ca4da6fe54529c27c14cea8b2',
        'pageNo': '1',
        'numOfRows': '1000', # 한 번에 가져올 최대 데이터 수
        'LAWD_CD': lawd_cd,
        'DEAL_YMD': deal_ymd
    }

    # API 서버에 데이터 요청하기
    response = requests.get(url, params=params)
    
    # 정상적으로 응답을 받았을 경우 (상태코드 200)
    if response.status_code == 200:
        # XML 형태의 데이터를 파이썬이 읽기 쉽게 변환
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        if items:
            data = []
            for item in items:
                # 필요한 데이터만 뽑아내기
                apt_name = item.find('아파트').text if item.find('아파트') is not None else ''
                price = item.find('거래금액').text if item.find('거래금액') is not None else ''
                area = item.find('전용면적').text if item.find('전용면적') is not None else ''
                floor = item.find('층').text if item.find('층') is not None else ''
                day = item.find('일').text if item.find('일') is not None else ''
                
                # 표(DataFrame)로 만들기 위해 리스트에 저장
                data.append({
                    '아파트명': apt_name.strip(),
                    '거래금액(만원)': price.strip(),
                    '전용면적(㎡)': area,
                    '층': floor,
                    '거래일': f"{day.zfill(2)}일"
                })
            
            # 엑셀과 같은 표(DataFrame) 형태로 변환
            df = pd.DataFrame(data)
            
            # 3. 특정 아파트만 발라내기(필터링)
            if target_apt:
                # 입력한 아파트 이름이 포함된 데이터만 남김
                filtered_df = df[df['아파트명'].str.contains(target_apt, na=False)]
                st.subheader(f"🔍 '{target_apt}' 검색 결과: 총 {len(filtered_df)}건")
                st.dataframe(filtered_df, use_container_width=True)
            else:
                # 검색어를 입력하지 않으면 해당 지역 전체 데이터 출력
                st.subheader(f"전체 거래 내역: 총 {len(df)}건")
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("해당 조건에 맞는 거래 데이터가 없습니다.")
    else:
        st.error(f"데이터를 불러오지 못했습니다. (오류 코드: {response.status_code})")
