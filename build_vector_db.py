import json
import chromadb
from chromadb.utils import embedding_functions

# 1. 한국어 임베딩 모델 설정
# 허깅페이스(HuggingFace)에서 한국어 문장 유사도 측정에 많이 쓰이는 오픈소스 모델입니다.
model_name = "jhgan/ko-sroberta-multitask"
sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=model_name)

# 2. ChromaDB 초기화 (로컬 폴더에 데이터 영구 저장)
print("ChromaDB를 초기화합니다...")
client = chromadb.PersistentClient(path="./chroma_db") # 현재 폴더 아래 chroma_db 폴더 생성

# 컬렉션(RDBMS의 테이블 같은 개념) 생성
collection = client.get_or_create_collection(
    name="jumpit_jobs",
    embedding_function=sentence_transformer_ef
)

# 3. JSON 데이터 불러오기
with open('./clawler/jumpit_final_data_page1.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

documents = []  # 임베딩할 실제 텍스트 내용
metadatas = []  # 검색 결과로 보여줄 추가 정보
ids = []        # 각 데이터의 고유 ID

print(f"총 {len(jobs)}개의 공고 데이터를 벡터화 준비 중...")

# 4. 데이터를 벡터 DB 구조에 맞게 가공
for job in jobs:
    # 추천의 핵심이 되는 텍스트들만 묶어서 하나의 문서(Document)로 만듭니다.
    tech_stacks = ", ".join(job.get('techStacks', [])) if isinstance(job.get('techStacks'), list) else job.get('techStacks', '')

    doc_text = f"직무: {job.get('jobCategory', '')}\n기술스택: {tech_stacks}\n주요업무: {job.get('주요업무', '')}\n자격요건: {job.get('자격요건', '')}"
    documents.append(doc_text)

    # 검색된 후 화면에 뿌려주거나 필터링에 사용할 메타데이터 저장
    metadatas.append({
        "title": job.get('title', ''),
        "companyName": job.get('companyName', ''),
        "url": f"https://jumpit.saramin.co.kr/position/{job.get('id')}"
    })

    ids.append(str(job.get('id')))

# 5. DB에 데이터 삽입 (이 과정에서 자동으로 임베딩 모델이 텍스트를 벡터로 변환합니다)
print("문서들을 임베딩하여 Vector DB에 저장하고 있습니다. (시간이 조금 걸릴 수 있습니다.)")
collection.add(
    documents=documents,
    metadatas=metadatas,
    ids=ids
)

print("\n✅ Vector DB 구축이 완료되었습니다! 현재 폴더에 'chroma_db' 폴더가 생성되었는지 확인하세요.")