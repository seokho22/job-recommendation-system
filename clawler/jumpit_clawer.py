import requests
from bs4 import BeautifulSoup
import json
import time # 서버 차단을 막기 위한 휴식용 라이브러리 추가

def get_position_details(position_id):
    """특정 공고 ID의 상세 정보를 HTML 파싱하여 반환합니다."""
    url = f"https://jumpit.saramin.co.kr/position/{position_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    # 기본값 세팅 (페이지가 없거나 에러가 날 경우 빈 문자열 반환)
    details = {
        "주요업무": "",
        "자격요건": "",
        "우대사항": "",
        "복지 및 혜택": "",
        "학력": ""
    }

    if response.status_code != 200:
        return details

    soup = BeautifulSoup(response.text, 'html.parser')
    dt_tags = soup.find_all('dt')

    for dt in dt_tags:
        title = dt.text.strip()
        if title in details:
            dd_tag = dt.find_next_sibling('dd')
            if dd_tag:
                pre_tag = dd_tag.find('pre')
                if pre_tag:
                    details[title] = pre_tag.text.strip()
                else:
                    details[title] = dd_tag.text.strip()

    return details

def crawl_and_merge_jumpit_jobs(page=1):
    """API 목록 데이터와 상세 데이터를 병합하여 최종 JSON으로 저장합니다."""
    url = f"https://jumpit-api.saramin.co.kr/api/positions?sort=reg_dt&highlight=false&page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    print(f"📊 {page}페이지 목록 데이터 수집 시작...")
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ API 호출 에러 발생: {response.status_code}")
        return

    data = response.json()
    positions = data.get('result', {}).get('positions', [])

    if not positions:
        print("수집할 공고가 없습니다.")
        return

    merged_data_list = []
    total_count = len(positions)

    # 리스트에 있는 각 공고들을 하나씩 순회합니다.
    for idx, pos in enumerate(positions):
        job_id = pos.get('id')
        print(f"[{idx+1}/{total_count}] 공고 ID {job_id} 병합 중...")

        # 1. API 리스트에서 필요한 데이터만 추출
        basic_info = {
            "id": job_id,
            "jobCategory": pos.get("jobCategory", ""),
            "title": pos.get("title", ""),
            "companyName": pos.get("companyName", ""),
            "techStacks": pos.get("techStacks", []),
            "minCareer": pos.get("minCareer", 0),
            "maxCareer": pos.get("maxCareer", 0),
            "locations": pos.get("locations", []),
            "closedAt": pos.get("closedAt", "")
        }

        # 2. 해당 ID의 상세 페이지 파싱 데이터 가져오기
        details_info = get_position_details(job_id)

        # 3. 기본 정보와 상세 정보를 하나의 딕셔너리로 합치기 (Python Dictionary Unpacking 활용)
        merged_info = {**basic_info, **details_info}
        merged_data_list.append(merged_info)

        # ⚠️ 아주 중요: 짧은 시간에 너무 많은 상세 페이지를 요청하면 IP가 차단될 수 있습니다.
        # 공고 1개를 수집할 때마다 0.5초씩 쉬어줍니다.
        time.sleep(0.5)

        # 4. 최종 병합된 리스트를 JSON 파일로 저장
    filename = f"jumpit_final_data_page{page}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(merged_data_list, f, ensure_ascii=False, indent=4)

    print(f"\n✅ 데이터 수집 및 병합 완료! [{filename}] 파일이 생성되었습니다.")

# 실행
if __name__ == "__main__":
    # 1페이지 데이터 병합 실행
    crawl_and_merge_jumpit_jobs(page=1)