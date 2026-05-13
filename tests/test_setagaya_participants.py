import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from app.municipal_modules.setagaya.committee.parsers.setagaya_committee_parser import (
    SetagayaCommitteeParser,
)

def test_extracts_participants():
    text = Path("app/raw_minutes/SetagayaCommitteeFetcher__R070519480214.txt").read_text(encoding="cp932")
    parser = SetagayaCommitteeParser()
    data = parser.extract_meeting_data(text)
    assert "下山芳男" in data["participants"]
