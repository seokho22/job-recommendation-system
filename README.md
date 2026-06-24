# 🚀 점핏(Jumpit) 맞춤형 채용 공고 추천 시스템

> 비정형 데이터인 구직자의 PDF 이력서를 LLM으로 구조화하고, 채용 플랫폼 '점핏'의 공고 데이터와 시맨틱 검색(Semantic Search) 기술을 매칭하여 가장 적합한 직무 및 채용 공고 Top 5를 추천하는 파이프라인입니다.

---

## 1. 프로젝트 개요

### 1-1. 프로젝트 주제 및 개발 목적
* **주제**: 구직자 맞춤형 채용 공고 추천 엔진 개발
* **목적**: 문맥을 이해하는 시맨틱 매칭 파이프라인을 구축하여 구직자에게는 적합한 공고를 제안하고, 정보 탐색 시간을 단축하고자 합니다.

### 1-2. 핵심 기능
1. **점핏(Jumpit) 공고 데이터 수집**: 봇 차단 및 네트워크 지연 리스크를 최소화하며 최신 공고의 기술 스택, 주요 업무, 자격 요건을 마이닝합니다.
2. **LLM 기반 이력서 파싱 (Structured Output)**: PyMuPDF로 이력서 텍스트를 추출한 뒤, `gpt-4o-mini`와 Pydantic 스키마를 결합하여 비정형 데이터를 완벽한 JSON 프로필로 정형화합니다.
3. **벡터 데이터베이스 인덱싱**: 한국어 문맥에 특화된 `ko-sroberta` 임베딩 모델을 활용해 공고 데이터를 벡터화하고 `ChromaDB`에 영구 저장합니다.
4. **유사도 랭킹 기반 추천**: 추출된 이력서의 핵심 역량을 쿼리로 변환하여, 벡터 공간 상에서 유클리드 거리가 가장 가까운 상위 5개의 맞춤형 공고 및 URL을 제공합니다.

---

## 2. 시작 가이드 (Installation & Running)

### 5-1. 요구 사항 및 기술 스택
* **Language**: Python 3.10+
* **Framework/Libraries**: OpenAI API, ChromaDB, PyMuPDF (fitz), Beautifulsoup4, SentenceTransformers

### 5-2. 환경 변수 설정 (`.env`)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 OpenAI API 키를 입력합니다.
```env
OPENAI_API_KEY=your_openai_api_key_here
```
### 5-3. 실행 방법
```Bash
# 1. 의존성 라이브러리 설치
pip install -r requirements.txt

# 2. 채용 공고 실시간 크롤링 (json 생성)
python jumpit_clawer.py

# 3. 데이터 전처리 및 로컬 ChromaDB 빌드
python build_vector_db.py

# 4. 내 이력서(resume.pdf) 기반 공고 추천 실행
python recommend_pipeline.py
```