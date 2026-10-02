import requests
import xml.etree.ElementTree as ET

# 1. 🔍 검색하고 싶은 지역과 월을 설정하세요!
lawd_cd = '11380'     # 11380: 은평구, 11410: 서대문구
deal_ymd = '202608'   # 확인하고 싶은 연도와 월 (예: 2026년 8월)

# 공공데이터포털 API 인증키
service_key = '014e8e30437cc041035a920222ccefa9300b972ca4da6fe54529c27c14cea8b2'

url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade"
params = {
    'serviceKey': service_key,
    'pageNo': '1',
    'numOfRows': '1000', # 넉넉하게 1000건 조회
    'LAWD_CD': lawd_cd,
    'DEAL_YMD': deal_ymd
}

print(f"🚀 [{deal_ymd}] 기준, 지역코드 [{lawd_cd}]의 아파트 실거래 명칭을 수집합니다...\n")

# API 호출
response = requests.get(url, params=params)

if response.status_code == 200:
    root = ET.fromstring(response.content)
    items = root.findall('.//item')
    
    # 중복 이름을 제거하기 위해 set()을 사용합니다.
    apt_names = set() 
    
    for item in items:
        # 국토부 데이터의 aptNm(아파트명) 태그 값을 가져옵니다.
        apt_name = item.find('aptNm').text.strip() if item.find('aptNm') is not None else ''
        if apt_name:
            apt_names.add(apt_name)
            
    print("✅ 해당 월에 거래된 아파트의 국토부 공식 명칭 목록입니다 (가나다순):")
    print("-" * 50)
    
    # 가나다 순으로 정렬해서 예쁘게 출력합니다.
    for name in sorted(apt_names):
        print(f"- {name}")
        
    print("-" * 50)
    print(f"총 {len(apt_names)}개의 아파트 단지 명칭을 찾았습니다!")
else:
    print(f"❌ API 호출 실패! 에러 코드: {response.status_code}")
