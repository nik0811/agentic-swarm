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
        strategy: Literal["fixed", "recursive", "semantic", "code"] = "recursive",
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
        elif self.strategy == "code":
            return self._chunk_code(text, metadata)
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

    def _chunk_code(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Code-aware chunking that splits by functions, classes, and methods."""
        import re
        metadata = metadata or {}
        chunks = []
        index = 0

        patterns = [
            r'^(class\s+\w+[^:]*:.*?)(?=\nclass\s|\n(?![ \t])(?!\s*$)\S|\Z)',
            r'^((?:async\s+)?def\s+\w+[^:]*:.*?)(?=\n(?:async\s+)?def\s|\nclass\s|\n(?![ \t])(?!\s*$)\S|\Z)',
        ]

        class_pattern = re.compile(
            r'^(class\s+\w+[^:]*:.*?)(?=^class\s|\Z)',
            re.MULTILINE | re.DOTALL,
        )
        func_pattern = re.compile(
            r'^((?:async\s+)?def\s+\w+[^:]*:.*?)(?=^(?:async\s+)?def\s|^class\s|\Z)',
            re.MULTILINE | re.DOTALL,
        )

        class_matches = list(class_pattern.finditer(text))

        if class_matches:
            for match in class_matches:
                class_text = match.group(1).strip()
                class_name_match = re.match(r'class\s+(\w+)', class_text)
                class_name = class_name_match.group(1) if class_name_match else "unknown"

                if self._count_tokens(class_text) <= self.chunk_size:
                    chunks.append(Chunk(
                        content=class_text,
                        index=index,
                        metadata={**metadata, "type": "class", "name": class_name},
                        token_count=self._count_tokens(class_text),
                    ))
                    index += 1
                else:
                    method_pattern = re.compile(
                        r'^(    (?:async\s+)?def\s+\w+[^:]*:.*?)(?=^    (?:async\s+)?def\s|\Z)',
                        re.MULTILINE | re.DOTALL,
                    )
                    methods = list(method_pattern.finditer(class_text))

                    if methods:
                        header_end = methods[0].start()
                        header = class_text[:header_end].strip()
                        if header:
                            chunks.append(Chunk(
                                content=header,
                                index=index,
                                metadata={**metadata, "type": "class_header", "name": class_name},
                                token_count=self._count_tokens(header),
                            ))
                            index += 1

                        for m in methods:
                            method_text = m.group(1).strip()
                            method_name_match = re.match(r'\s*(?:async\s+)?def\s+(\w+)', method_text)
                            method_name = method_name_match.group(1) if method_name_match else "unknown"

                            chunks.append(Chunk(
                                content=method_text,
                                index=index,
                                metadata={**metadata, "type": "method", "class": class_name, "name": method_name},
                                token_count=self._count_tokens(method_text),
                            ))
                            index += 1
                    else:
                        sub_chunks = self._chunk_recursive(class_text, {**metadata, "type": "class", "name": class_name})
                        for sc in sub_chunks:
                            sc.index = index
                            index += 1
                        chunks.extend(sub_chunks)
        else:
            func_matches = list(func_pattern.finditer(text))
            if func_matches:
                preamble_end = func_matches[0].start()
                preamble = text[:preamble_end].strip()
                if preamble and self._count_tokens(preamble) > 10:
                    chunks.append(Chunk(
                        content=preamble,
                        index=index,
                        metadata={**metadata, "type": "module_header"},
                        token_count=self._count_tokens(preamble),
                    ))
                    index += 1

                for match in func_matches:
                    func_text = match.group(1).strip()
                    func_name_match = re.match(r'(?:async\s+)?def\s+(\w+)', func_text)
                    func_name = func_name_match.group(1) if func_name_match else "unknown"

                    if self._count_tokens(func_text) <= self.chunk_size:
                        chunks.append(Chunk(
                            content=func_text,
                            index=index,
                            metadata={**metadata, "type": "function", "name": func_name},
                            token_count=self._count_tokens(func_text),
                        ))
                        index += 1
                    else:
                        sub_chunks = self._chunk_recursive(func_text, {**metadata, "type": "function", "name": func_name})
                        for sc in sub_chunks:
                            sc.index = index
                            index += 1
                        chunks.extend(sub_chunks)
            else:
                return self._chunk_recursive(text, metadata)

        if not chunks:
            return self._chunk_recursive(text, metadata)

        return chunks

