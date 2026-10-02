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
last_month = today - relativedelta(months=1)
default_month_str = last_month.strftime("%Y%m")

# 드롭다운용 최근 3년(36개월) 월 리스트 생성
month_list = [(today - relativedelta(months=i)).strftime("%Y%m") for i in range(36)]

# 최근 3개월 전 날짜 계산 (기준가 산정용)
three_months_ago = today - relativedelta(months=3)
three_months_ago_str = three_months_ago.strftime("%Y-%m") # 예: 2026-07

# 3. 사이드바 UI 설정
st.sidebar.header("검색 조건 설정")
st.sidebar.info("📌 지역: 은평구, 서대문구 자동 조회")

st.sidebar.subheader("조회 기간")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_month = st.selectbox("시작 월", month_list[::-1], index=month_list[::-1].index(default_month_str))
with col2:
    end_month = st.selectbox("종료 월", month_list[::-1], index=month_list[::-1].index(default_month_str))

target_area = st.sidebar.text_input("기본 전용면적(㎡) (예: 59)", "59")
st.sidebar.caption("※ 무악청구1차, 홍제한양은 자동으로 84㎡가 조회됩니다.")

# 비교할 아파트 목록 세팅
default_apts = [
    "북한산힐스테이트7차", "북한산현대힐스테이트3차", "래미안베라힐즈", "불광롯데캐슬",
    "돈의문센트레빌", "녹번역e편한세상캐슬", "은평뉴타운박석고개힐스테이트1단지",
    "e편한세상서대문", "북한산더샵", "무악청구1차", "홍제한양"
]
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
lawd_cd_list = ['11380', '11410'] # 은평구, 서대문구 코드

with st.spinner('은평구 및 서대문구의 데이터를 불러오는 중입니다... (조금만 기다려주세요)'):
    for ymd in months_to_fetch:
        for lawd_cd in lawd_cd_list:
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
                    
                    # 선택된 아파트 중 하나인지 확인
                    if any(apt in apt_name for apt in selected_apts):
                        area = item.find('excluUseAr').text if item.find('excluUseAr') is not None else '0'
                        area_prefix = str(area).split('.')[0]
                        
                        # 특정 아파트(무악청구1차, 홍제한양)는 무조건 84㎡로 필터링, 나머지는 target_area로 필터링
                        is_target_area = False
                        if "무악청구" in apt_name or "홍제한양" in apt_name:
                            if area_prefix == "84":
                                is_target_area = True
                        else:
                            if area_prefix == target_area.strip():
                                is_target_area = True
                        
                        # 조건에 맞는 면적일 경우에만 데이터 추가
                        if is_target_area:
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
        # 모든 거래내역을 담은 원본 데이터프레임
        raw_df = pd.DataFrame(all_data)
        
        # 🌟 [핵심 수정 로직] 최근 3개월 데이터만 필터링 후 아파트별 '최고가 1건'만 추출
        recent_df = raw_df[raw_df['계약월'] >= three_months_ago_str].copy()
        
        if not recent_df.empty:
            # groupby로 아파트별로 묶은 뒤, 거래금액이 가장 큰(idxmax) 행의 인덱스를 찾습니다.
            max_price_idx = recent_df.groupby('아파트명')['거래금액(만원)'].idxmax()
            
            # 찾은 인덱스를 바탕으로 최고가 행들만 추려냅니다. (이게 우리가 볼 최종 요약표입니다)
            top_price_df = recent_df.loc[max_price_idx].copy()
            
            # 북힐7차 데이터 추출 (최고가)
            our_apt_df = top_price_df[top_price_df['아파트명'].str.contains('북한산힐스테이트7차')]
            
            if not our_apt_df.empty:
                our_base_price = our_apt_df['거래금액(만원)'].max()
                
                # 차액 계산
                top_price_df['우리집 3개월 최고가대비 차액'] = top_price_df['거래금액(만원)'] - our_base_price
                top_price_df['우리집 3개월 최고가대비 차액'] = top_price_df['우리집 3개월 최고가대비 차액'].apply(
                    lambda x: f"🔺 +{int(x):,}만원" if x > 0 else (f"🔻 {int(x):,}만원" if x < 0 else "-")
                )
                
                st.info(f"💡 기준가 설정 완료: **북한산힐스테이트7차**의 최근 3개월({three_months_ago_str} ~ 현재) **최고 실거래가는 {int(our_base_price):,}만원**입니다.")
            else:
                top_price_df['우리집 3개월 최고가대비 차액'] = "최고가 산정불가"
                st.warning(f"⚠️ 최근 3개월({three_months_ago_str} ~ 현재) 내 '북한산힐스테이트7차' 거래가 없어 기준가를 계산할 수 없습니다.")

            # 최종 표 데이터 정렬 및 천 단위 콤마
            top_price_df['거래금액(만원)'] = top_price_df['거래금액(만원)'].apply(lambda x: f"{x:,}")
            top_price_df = top_price_df.sort_values(by=['거래금액(만원)'], ascending=False)
            
            st.success(f"조회 완료: 선택한 아파트 중 최근 3개월 거래가 있는 총 {len(top_price_df)}개 단지의 '최고가' 비교")
            st.dataframe(top_price_df, use_container_width=True, hide_index=True)
            
        else:
            st.warning(f"최근 3개월({three_months_ago_str} ~ 현재) 내 거래된 데이터가 없습니다.")

        st.write("---")
        
        # 🌟 [신규 추가] 원본 데이터(로그)를 확인하고 검증할 수 있는 펼침 메뉴
        with st.expander("🔍 전체 원본 거래 로그 보기 (어떤 거래들이 있었는지 확인해보세요!)"):
            st.write("국토부 API에서 불러온 **선택 기간 내 모든 거래 내역**입니다. 누락되거나 의심되는 데이터가 있다면 여기서 확인해보세요.")
            # 원본 데이터도 보기 좋게 콤마 정렬
            display_raw_df = raw_df.copy()
            display_raw_df = display_raw_df.sort_values(by=['아파트명', '계약월', '거래일'], ascending=[True, False, False])
            st.dataframe(display_raw_df, use_container_width=True, hide_index=True)

    else:
        st.warning("선택한 기간 내 조건에 맞는 거래 데이터가 없습니다. (국토부에 신고된 실거래가 없는 경우일 수 있습니다.)")
