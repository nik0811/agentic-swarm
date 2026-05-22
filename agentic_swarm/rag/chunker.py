from typing import List, Literal
from pydantic import BaseModel


class Chunk(BaseModel):
    content: str
    index: int
    metadata: dict = {}
    token_count: int = 0


class Chunker:
    """Split documents into chunks for embedding."""
    
    def __init__(
        self,
        strategy: Literal["fixed", "recursive", "semantic"] = "recursive",
        chunk_size: int = 512,
        overlap: int = 50,
    ):
        self.strategy = strategy
        self.chunk_size = chunk_size
        self.overlap = overlap
        self._token_counter = None
    
    def _get_token_counter(self):
        if self._token_counter is None:
            try:
                import tiktoken
                self._token_counter = tiktoken.get_encoding("cl100k_base")
            except ImportError:
                self._token_counter = None
        return self._token_counter
    
    def _count_tokens(self, text: str) -> int:
        counter = self._get_token_counter()
        if counter:
            return len(counter.encode(text))
        return len(text.split())
    
    def chunk(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Split text into chunks."""
        if self.strategy == "fixed":
            return self._chunk_fixed(text, metadata)
        elif self.strategy == "recursive":
            return self._chunk_recursive(text, metadata)
        elif self.strategy == "semantic":
            return self._chunk_semantic(text, metadata)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")
    
    def _chunk_fixed(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Split by fixed token count with overlap."""
        counter = self._get_token_counter()
        if counter:
            tokens = counter.encode(text)
            chunks = []
            start = 0
            index = 0
            
            while start < len(tokens):
                end = min(start + self.chunk_size, len(tokens))
                chunk_tokens = tokens[start:end]
                chunk_text = counter.decode(chunk_tokens)
                
                chunks.append(Chunk(
                    content=chunk_text,
                    index=index,
                    metadata=metadata or {},
                    token_count=len(chunk_tokens),
                ))
                
                start = end - self.overlap if end < len(tokens) else end
                index += 1
            
            return chunks
        else:
            words = text.split()
            chunks = []
            start = 0
            index = 0
            
            while start < len(words):
                end = min(start + self.chunk_size, len(words))
                chunk_text = " ".join(words[start:end])
                
                chunks.append(Chunk(
                    content=chunk_text,
                    index=index,
                    metadata=metadata or {},
                    token_count=end - start,
                ))
                
                start = end - self.overlap if end < len(words) else end
                index += 1
            
            return chunks
    
    def _chunk_recursive(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Split by structure (headers, paragraphs, sentences)."""
        separators = ["\n\n", "\n", ". ", " "]
        return self._recursive_split(text, separators, metadata or {}, 0)
    
    def _recursive_split(
        self,
        text: str,
        separators: List[str],
        metadata: dict,
        start_index: int,
    ) -> List[Chunk]:
        chunks = []
        
        if self._count_tokens(text) <= self.chunk_size:
            if text.strip():
                return [Chunk(
                    content=text.strip(),
                    index=start_index,
                    metadata=metadata,
                    token_count=self._count_tokens(text),
                )]
            return []
        
        if not separators:
            return [Chunk(
                content=text[:self.chunk_size * 4].strip(),
                index=start_index,
                metadata=metadata,
                token_count=self._count_tokens(text[:self.chunk_size * 4]),
            )]
        
        separator = separators[0]
        parts = text.split(separator)
        
        current_chunk = ""
        current_index = start_index
        
        for part in parts:
            if not part.strip():
                continue
                
            test_chunk = current_chunk + separator + part if current_chunk else part
            
            if self._count_tokens(test_chunk) <= self.chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk.strip():
                    chunks.append(Chunk(
                        content=current_chunk.strip(),
                        index=current_index,
                        metadata=metadata,
                        token_count=self._count_tokens(current_chunk),
                    ))
                    current_index += 1
                
                if self._count_tokens(part) <= self.chunk_size:
                    current_chunk = part
                else:
                    sub_chunks = self._recursive_split(
                        part, separators[1:], metadata, current_index
                    )
                    chunks.extend(sub_chunks)
                    current_index += len(sub_chunks)
                    current_chunk = ""
        
        if current_chunk.strip():
            chunks.append(Chunk(
                content=current_chunk.strip(),
                index=current_index,
                metadata=metadata,
                token_count=self._count_tokens(current_chunk),
            ))
        
        return chunks
    
    def _chunk_semantic(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Split by semantic similarity (simplified version)."""
        return self._chunk_recursive(text, metadata)
    
    def chunk_file(self, path: str) -> List[Chunk]:
        """Chunk a file."""
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        
        return self.chunk(text, metadata={"source": path})
