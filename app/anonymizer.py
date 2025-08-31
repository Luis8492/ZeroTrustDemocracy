import os
from typing import Iterable, Optional


class Anonymizer:
    PIIList = []

    def __init__(self, pii_files: Optional[Iterable[str]] = None):
        self.PIIList = []
        if pii_files is not None:
            self.build_from_files(pii_files)
        else:
            self.pii_dir = 'PIIs'
            self.build_from_dir()

    def build_from_dir(self):
        if not os.path.exists(self.pii_dir):
            raise FileNotFoundError(f"PIIディレクトリが見つかりません: {self.pii_dir}")
        for filename in os.listdir(self.pii_dir):
            file_path = os.path.join(self.pii_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.PIIList.extend([line.strip() for line in f if line.strip()])

    def build_from_files(self, pii_files: Iterable[str]):
        for file_path in pii_files:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"PIIファイルが見つかりません: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                self.PIIList.extend([line.strip() for line in f if line.strip()])
    
    def anonymize_comment(self, comment: str) -> str:
        for PII in self.PIIList:
            comment = comment.replace(PII, "***")
        return comment
