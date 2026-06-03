import requests
from bs4 import BeautifulSoup
import json
import time
from tqdm import tqdm  # 진행 상황을 표시하기 위한 라이브러리 추가

def get_position_details(position_id):
    """특정 공고 ID의 상세 정보를 HTML 파싱하여 반환합니다."""
    url = f"https://jumpit.saramin.co.kr/position/{position_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

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

def crawl_jumpit_jobs_by_page(page=1):
    """특정 페이지의 API 목록 데이터와 상세 데이터를 병합한 리스트를 반환합니다."""
    url = f"https://jumpit-api.saramin.co.kr/api/positions?sort=reg_dt&highlight=false&page={page}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ API 호출 에러 발생: {response.status_code}")
        return None

    data = response.json()
    positions = data.get('result', {}).get('positions', [])

    if not positions:
        print(f"ℹ️ {page}페이지에 더 이상 수집할 공고가 없습니다.")
        return []

    page_data_list = []

    # 🌟 tqdm 적용 부분: 기존의 print 문을 제거하고 for문에 tqdm을 씌워줍니다.
    for pos in tqdm(positions, desc=f"⏳ {page}페이지 공고 수집", unit="개", ncols=80):
        job_id = pos.get('id')

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

        details_info = get_position_details(job_id)
        merged_info = {**basic_info, **details_info}
        page_data_list.append(merged_info)

        time.sleep(0.5)

    return page_data_list

# 실행부
if __name__ == "__main__":
    current_page = 1
    all_merged_jobs = []

    print("🚀 전체 데이터 크롤링을 시작합니다...\n")

    while True:
        # 1. 해당 페이지 데이터 가져오기 (이 안에서 tqdm 바가 작동합니다)
        page_jobs = crawl_jumpit_jobs_by_page(page=current_page)

        if page_jobs is None or len(page_jobs) == 0:
            print("\n🏁 모든 데이터 수집이 완료되었습니다. 저장을 시작합니다.")
            break

        # 2. 전체 리스트에 현재 페이지 데이터 누적하기
        all_merged_jobs.extend(page_jobs)
        print(f"✔️ {current_page}페이지 완료! 현재까지 누적된 총 공고 수: {len(all_merged_jobs)}개\n")

        # 3. 다음 페이지로 변경 및 페이지 간 휴식
        current_page += 1
        time.sleep(2)

    # 4. JSON 파일로 통합 저장
    if all_merged_jobs:
        filename = "jumpit_all_pages_combined.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_merged_jobs, f, ensure_ascii=False, indent=4)
        print(f"✅ [성공] 총 {len(all_merged_jobs)}개의 공고 데이터가 [{filename}] 파일로 통합 저장되었습니다.")
    else:
        print("❌ 수집된 데이터가 없어 파일을 생성하지 않았습니다.")