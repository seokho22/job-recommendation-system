import os
import json
import fitz  # PyMuPDF 라이브러리
from openai import OpenAI
from pydantic import BaseModel
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

# ==========================================
# 1. PDF에서 텍스트 추출 단계
# ==========================================
def extract_text_from_pdf(pdf_path):
    """PDF 파일 경로를 받아 내부의 모든 텍스트를 추출합니다."""
    if not os.path.exists(pdf_path):
        print(f"❌ 파일을 찾을 수 없습니다: {pdf_path}")
        return None

    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

# ==========================================
# 2. GPT-4o mini 구조화 JSON 스키마 정의 단계
# ==========================================
class ResumeProfile(BaseModel):
    """LLM이 이력서에서 오차 없이 정확하게 추출해야 할 데이터 구조를 정의합니다."""
    job_category: str      # 희망 직무 (예: 백엔드 개발자, 인공지능 엔지니어)
    tech_stacks: list[str]  # 보유 기술 스택 리스트 (예: ["Python", "PyTorch"])
    experience_years: int  # 경력 년수 (신입은 0)
    project_summary: str   # 주요 프로젝트 및 경력 사항 요약 문장

# ==========================================
# 3. GPT-4o mini 기반 정보 구조화 단계
# ==========================================
def parse_resume_with_llm(raw_text):
    # .env 파일의 환경 변수를 메모리로 로드합니다.
    load_dotenv()
    client = OpenAI()

    print("🧠 GPT-4o mini가 이력서 정보를 분석하고 구조화하는 중...")

    # .parse()와 response_format을 이용해 Pydantic 모델 형태의 출력을 보장받습니다.
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "당신은 채용 시스템의 AI 리크루터입니다. 구직자의 이력서 텍스트를 분석하여 핵심 프로필 정보만 명확하게 추출해야 합니다."
            },
            {"role": "user", "content": f"다음 이력서 원본 텍스트에서 정보를 추출해 주세요:\n\n{raw_text}"}
        ],
        response_format=ResumeProfile,
    )

    # 구조화되어 리턴된 데이터 파싱 결과 객체 반환
    return completion.choices[0].message.parsed

# ==========================================
# 4. 벡터 DB 검색 및 공고 추천 단계
# ==========================================
def search_similar_jobs(resume_profile, chroma_path="./chroma_db"):
    """구조화된 이력서 데이터를 기반으로 벡터 DB에서 가장 유사한 채용 공고를 검색합니다."""
    # 기존 DB 구축 시 사용했던 한국어 문장 임베딩 모델과 동일하게 세팅
    model_name = "jhgan/ko-sroberta-multitask"
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

    # 로컬 ChromaDB 연결 및 컬렉션 로드
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection(name="jumpit_jobs", embedding_function=sentence_transformer_ef)

    # 이력서의 핵심 요소들을 매칭 성능이 가장 잘 나오도록 하나의 문장 쿼리로 조합합니다.
    skills_str = ", ".join(resume_profile.tech_stacks)
    search_query = (
        f"직무: {resume_profile.job_category}\n"
        f"기술스택: {skills_str}\n"
        f"주요 경험 및 요약: {resume_profile.project_summary}"
    )

    print("\n🔍 생성된 벡터 검색용 임베딩 쿼리:")
    print("-" * 40)
    print(search_query)
    print("-" * 40)

    # 유사도 대조 검색 실행 (상위 5개 추출)
    results = collection.query(
        query_texts=[search_query],
        n_results=5
    )
    return results

# ==========================================
# 전체 파이프라인 실행 테스트
# ==========================================
if __name__ == "__main__":
    # 테스트용 이력서 PDF 파일 경로
    my_resume_pdf = "./data/my_resume.pdf"

    # 1단계: PDF에서 텍스트 추출
    print("1. 이력서 PDF 파일 읽는 중...")
    extracted_text = extract_text_from_pdf(my_resume_pdf)

    if extracted_text:
        # 2단계: LLM을 이용해 정형 JSON 데이터로 가공
        print("\n2. 가공되지 않은 텍스트를 LLM 구조화 데이터로 변환 중...")
        structured_resume = parse_resume_with_llm(extracted_text)

        # 가공된 데이터 확인해보기
        print("\n✨ 추출된 구조화 JSON 데이터 결과:")
        print(structured_resume.model_dump_json(indent=4))

        # 3단계 & 4단계: 가공된 데이터를 바탕으로 벡터 DB에서 맞춤 공고 조회
        print("\n3. 벡터 DB 내 채용공고 유사도 비교 매칭 시작...")
        recommend_results = search_similar_jobs(structured_resume)

        # 최종 추천된 결과 화면에 출력하기
        print("\n🏆 [당신에게 딱 맞는 점핏 맞춤 공고 추천 결과] 🏆")
        print("=" * 60)
        for i in range(len(recommend_results['ids'][0])):
            distance = recommend_results['distances'][0][i]
            meta = recommend_results['metadatas'][0][i]

            print(f"[{i+1}순위 추천] {meta['companyName']} - {meta['title']}")
            print(f"   - 매칭 유사도 거리 계수: {distance:.4f}")
            print(f"   - 공고 바로가기 링크: {meta['url']}")
            print("-" * 60)