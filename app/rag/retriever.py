"""RAG 检索 - LangChain + Chroma"""

import os
from typing import List

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.schema import Document


class Retriever:
    def __init__(self, docs_dir: str = "docs", persist_dir: str = "chroma_db"):
        self.docs_dir = docs_dir
        self.persist_dir = persist_dir
        self._db = None
        self._init_db()

    def _init_db(self):
        # 如果已存在持久化数据，直接加载
        if os.path.exists(self.persist_dir) and os.listdir(self.persist_dir):
            self._db = Chroma(
                persist_directory=self.persist_dir,
            )
            return

        # 否则从 docs 目录加载并创建
        documents = []
        if os.path.exists(self.docs_dir):
            for fname in os.listdir(self.docs_dir):
                if fname.endswith(".md"):
                    path = os.path.join(self.docs_dir, fname)
                    loader = TextLoader(path, encoding="utf-8")
                    documents.extend(loader.load())

        if not documents:
            # 空知识库，创建一个占位文档
            documents = [Document(page_content="暂无知识库内容。")]

        splitter = CharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        chunks = splitter.split_documents(documents)

        self._db = Chroma.from_documents(
            chunks,
            persist_directory=self.persist_dir,
        )
        self._db.persist()

    def query(self, question: str, top_k: int = 3) -> str:
        if self._db is None:
            return ""
        docs = self._db.similarity_search(question, k=top_k)
        context = "\n---\n".join([d.page_content for d in docs])
        return context
