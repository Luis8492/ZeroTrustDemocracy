import os


class Anonymizer:
    """Replace personally identifiable information from comments."""

    def __init__(self, pii_dir: str):
        self.pii_dir = pii_dir
        self.pii_list: list[str] = []
        self.build_pii_list()

    def build_pii_list(self):
        if not os.path.exists(self.pii_dir):
            raise FileNotFoundError(f"PIIディレクトリが見つかりません: {self.pii_dir}")
        for filename in os.listdir(self.pii_dir):
            file_path = os.path.join(self.pii_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    pii_entries = [line.strip() for line in f if line.strip()]
                    self.pii_list.extend(pii_entries)

    def anonymize_comment(self, comment: str) -> str:
        for pii in self.pii_list:
            comment = comment.replace(pii, "***")
        return comment
