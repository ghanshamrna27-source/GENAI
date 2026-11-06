from dataclasses import asdict, dataclass

@dataclass
class Record:
    id: int
    category: str
    title: str
    keyword: str
    question: str
    answer: str
    source_url: str

    @classmethod
    def from_dict(cls, data):
        return cls(id=int(data["id"]), category=str(data.get("category", "General")),
                   title=str(data.get("title", "Untitled")), keyword=str(data.get("keyword", "")),
                   question=str(data.get("question", "")), answer=str(data.get("answer", "")),
                   source_url=str(data.get("source_url", "")))

    def to_dict(self):
        return asdict(self)
