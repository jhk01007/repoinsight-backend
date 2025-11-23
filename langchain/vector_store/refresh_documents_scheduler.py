from apscheduler.schedulers.background import BackgroundScheduler
from langchain.vector_store.pinecone_github_search_qualifier_store import PineconeGithubSearchQualifierStore

store = PineconeGithubSearchQualifierStore()

scheduler = BackgroundScheduler()

# 하루에 한 번 실행 (매 24시간)
scheduler.add_job(store.refresh_documents, "interval", hours=24)

def start_scheduler():
    scheduler.start()