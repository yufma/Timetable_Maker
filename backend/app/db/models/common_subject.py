from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base


class CommonSubject(Base):
    __tablename__ = "common_subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 구분: 핵심교양/일반교양/창의영역 등
    category: Mapped[str] = mapped_column(String(50), index=True)
    # 세부 영역 또는 묶음명
    area: Mapped[str] = mapped_column(String(100), index=True)
    # 과목 코드 및 명칭
    code: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
