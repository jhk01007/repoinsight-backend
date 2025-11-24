# **🔥 프로젝트 개요 (Overview)**

> **RepoInsight Backend**는 자연어 기반 검색을 처리하고 GitHub API 및 LLM 모델과 연동하여 정제된 검색 데이터를 제공하는 API 서버입니다.
> 
<br><br>
# **🏗 시스템 아키텍처 (System Architecture)**
<img width="2463" height="1590" alt="연습장 drawio" src="https://github.com/user-attachments/assets/a43b2a13-7355-411e-9e13-0f22c2819c4e" />

<br><br>

| 구성 요소 | 역할 |
|---|---|
| ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?logo=githubactions&logoColor=white) | 코드 변경 시 Docker 이미지 빌드 및 자동 배포 |
| ![AWS ECR](https://img.shields.io/badge/AWS_ECR-Container_Registry-FF9900?logo=amazonaws&logoColor=white) | 빌드된 Docker 이미지를 저장 및 관리 |
| ![AWS EC2](https://img.shields.io/badge/AWS_EC2-Compute_Instance-FF9900?logo=amazonaws&logoColor=white) | FastAPI 서버와 Redis 실행 환경 |
| ![Docker](https://img.shields.io/badge/Docker-Containerization-2496ED?logo=docker&logoColor=white) | FastAPI 및 Redis 컨테이너 구성 및 서비스 연동 |
| ![Nginx](https://img.shields.io/badge/NGINX+Certbot-HTTPS_Setup-009639?logo=nginx&logoColor=white) | 리버스 프록시 및 SSL(HTTPS) 적용 |


<br><br>
# **🔗 주요 기능 (Features)**

| **기능** | **설명** |
| --- | --- |
| 🔍 Repo 검색 API | LangChain + RAG 기반 Query Generation & Retrieval + GitHub API |
| 🧠 요약 생성 API | LLM 기반 Repo Summary 생성 |
| ⏱ 요청 최적화 | 속도 개선, 병렬 처리 |
| 🔐 Rate Limiting | Redis 기반 악의적/반복 요청 방어 |
| 💸 비용 최적화 | Token 절감 전략 적용 |


<br><br>
# **📁 프로젝트 구조 (Folder Structure)**

```bash
repoinsight-backend/
 ├─ 📁 .github/
 │   └─ 📁 workflows/          # CI/CD 워크플로우 설정
 ├─ 📁 common/                 # 공통 유틸, 설정, 공용 로직
 ├─ 📁 github/                 # GitHub API 연동 모듈
 ├─ 📁 langchain/              # LangChain · RAG 관련 체인/파이프라인
 ├─ 📁 schema/                 # 요청/응답 스키마 정의
 ├─ 📁 service/                # 도메인 서비스 계층 (비즈니스 로직)
 ├─ 📄 Dockerfile              # 컨테이너 이미지 빌드 설정
 ├─ 📄 compose.yml             # Docker Compose 정의
 ├─ 📄 main.py                 # FastAPI 앱 실행 진입점
 ├─ 📄 requirements.txt        # Python 의존성 리스트
 └─ 📄 __init__.py
```


<br><br>
## 🔒 환경 변수(Environment Variables)

| **변수명** | **설명** |
| --- | --- |
| OPENAI_API_KEY | OpenAI API 인증 키 |
| PINECONE_API_KEY | Pinecone 벡터DB 인증 키 |
| GIT_API_TOKEN | GitHub API 인증 토큰 |
| FRONTEND_URL | 배포된 프론트엔드 서비스 URL |
| REDIS_URL | Redis 연결 주소 |


<br><br>
# 📡 API 명세서 (API Specification)

| Endpoint | Method | Request Type | Required Fields | Success Response |
| --- | --- | --- | --- | --- |
| `/api/v1/repositories/search` | `POST` | Body(JSON) | `keyword (string, <=50)` | Repo 정보 리스트 (`name`, `summary`, `languages`, `stars`, `url`) |
| `/api/v1/repositories/languages/search` | `GET` | Query Param | `query (string, not empty)` | `list[str]` 언어 목록 |
