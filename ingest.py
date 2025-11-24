import arxiv
from src.services.ingest_service import IngestService

def ingest_data():
    print("🚀 Starting arXiv ingestion...")
    ingest = IngestService()

    client = arxiv.Client()
    search = arxiv.Search(
        query="retrieval augmented generation",
        max_results=20,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    for r in client.results(search):
        print("Indexing:", r.title)
        paper_id = r.entry_id.split("/")[-1]
        title = r.title
        abstract = r.summary
        authors = [a.name for a in r.authors]

        # Insert into graph directly
        ingest.gs.add_paper(
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            authors=authors,
            source="arXiv"
        )

        # Insert abstract as a single chunk for now
        ingest.vs.upsert_chunk(
            chunk_id=paper_id,
            text=f"{title}\n{abstract}",
            payload={
                "paper_id": paper_id,
                "title": title,
                "chunk_index": 0,
                "source": "arXiv"
            }
        )

    print("✅ arXiv ingestion complete.")

if __name__ == "__main__":
    ingest_data()
