import arxiv
from src.services.ingest_service import IngestService

def ingest_data():
    print("Starting arXiv ingestion...")
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

        ingest.ingest_text(
            paper_id=paper_id,
            title=title,
            text=f"{title}\n\n{abstract}",
            authors=authors,
            source="arXiv",
        )

    print("arXiv ingestion complete.")

if __name__ == "__main__":
    ingest_data()
