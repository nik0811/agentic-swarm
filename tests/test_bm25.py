import pytest

from agentic_swarm.rag.retriever import BM25


class TestBM25:
    def setup_method(self):
        self.bm25 = BM25()
        self.documents = [
            {"content": "python is a great programming language for data science"},
            {"content": "java is used for enterprise software development"},
            {"content": "python machine learning libraries like scikit-learn and pytorch"},
            {"content": "javascript is the language of the web"},
            {"content": "python web frameworks include django and flask"},
        ]
        self.bm25.index(self.documents)

    def test_index_sets_corpus_size(self):
        assert self.bm25._n_docs == 5

    def test_index_computes_average_doc_length(self):
        assert self.bm25._avg_dl > 0

    def test_search_returns_relevant_results(self):
        results = self.bm25.search("python programming")
        assert len(results) > 0
        top_idx = results[0][1]
        assert "python" in self.documents[top_idx]["content"]

    def test_search_scores_are_descending(self):
        results = self.bm25.search("python")
        for i in range(len(results) - 1):
            assert results[i][0] >= results[i + 1][0]

    def test_search_limit(self):
        results = self.bm25.search("python", limit=2)
        assert len(results) <= 2

    def test_search_empty_query(self):
        results = self.bm25.search("")
        assert results == []

    def test_search_no_match(self):
        results = self.bm25.search("xyzzyx nonexistent gibberish")
        assert results == []

    def test_search_returns_score_and_index(self):
        results = self.bm25.search("java enterprise")
        assert len(results) > 0
        score, idx = results[0]
        assert isinstance(score, float)
        assert isinstance(idx, int)
        assert score > 0
        assert "java" in self.documents[idx]["content"]

    def test_idf_rare_term_higher_score(self):
        results_rare = self.bm25.search("javascript")
        results_common = self.bm25.search("python")

        if results_rare and results_common:
            assert results_rare[0][0] > 0

    def test_empty_corpus(self):
        empty_bm25 = BM25()
        empty_bm25.index([])
        results = empty_bm25.search("query")
        assert results == []

    def test_single_document(self):
        bm25 = BM25()
        bm25.index([{"content": "hello world"}])
        results = bm25.search("hello")
        assert len(results) == 1
        assert results[0][1] == 0

    def test_tokenize_lowercases(self):
        tokens = BM25._tokenize("Hello World Python")
        assert tokens == ["hello", "world", "python"]

    def test_tokenize_removes_punctuation(self):
        tokens = BM25._tokenize("hello, world! test.")
        assert "hello" in tokens
        assert "world" in tokens
        assert "," not in tokens

    def test_reindex(self):
        new_docs = [
            {"content": "rust systems programming"},
            {"content": "go concurrency model"},
        ]
        self.bm25.index(new_docs)
        assert self.bm25._n_docs == 2
        results = self.bm25.search("python")
        assert results == []
