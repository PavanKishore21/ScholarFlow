from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import settings

def chunk_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    return splitter.split_text(text)
