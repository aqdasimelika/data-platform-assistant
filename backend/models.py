from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Step:
    type: str        # 'select' | 'input' | 'search' | 'suggest'
    node: str
    label: Optional[str] = None
    value: Optional[str] = None

    def to_dict(self):
        return asdict(self)
