import os
from datetime import datetime, timezone
from typing import Iterable, Optional

from sqlalchemy import Column, ForeignKey, Integer, String, Table, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, selectinload, sessionmaker

DB_PATH = os.getenv("PROMPT_DB_PATH", os.path.join(os.path.dirname(__file__), "..", "data", "prompts.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"


class Base(DeclarativeBase):
    pass


prompt_tags_table = Table(
    "prompt_tags",
    Base.metadata,
    Column("prompt_id", ForeignKey("prompts.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    summary: Mapped[str] = mapped_column(String, nullable=False)
    purpose: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    updated_at: Mapped[str] = mapped_column(String, nullable=False)
    tags: Mapped[list["Tag"]] = relationship("Tag", secondary=prompt_tags_table, back_populates="prompts")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    color: Mapped[str] = mapped_column(String, nullable=False)
    prompts: Mapped[list[Prompt]] = relationship("Prompt", secondary=prompt_tags_table, back_populates="tags")


engine = create_engine(
    DATABASE_URL,
    future=True,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _prompt_to_dict(prompt: Prompt) -> dict:
    return {
        "id": prompt.id,
        "title": prompt.title,
        "summary": prompt.summary,
        "purpose": prompt.purpose,
        "content": prompt.content,
        "created_at": prompt.created_at,
        "updated_at": prompt.updated_at,
    }


def _tag_to_dict(tag: Tag) -> dict:
    return {"id": tag.id, "name": tag.name, "color": tag.color}


def init_db() -> None:
    db_dir = os.path.dirname(DB_PATH) or "."
    os.makedirs(db_dir, exist_ok=True)
    Base.metadata.create_all(bind=engine)


def list_prompts(sort: str = "updated_desc", tag_id: Optional[int] = None) -> list[dict]:
    order_by_map = {
        "updated_desc": Prompt.updated_at.desc(),
        "created_desc": Prompt.created_at.desc(),
    }
    order_by = order_by_map.get(sort, order_by_map["updated_desc"])

    with SessionLocal() as session:
        stmt = select(Prompt)
        if tag_id is not None:
            stmt = stmt.join(Prompt.tags).where(Tag.id == tag_id).distinct()
        stmt = stmt.order_by(order_by)
        prompts = session.scalars(stmt).all()
        return [_prompt_to_dict(prompt) for prompt in prompts]


def get_prompt(prompt_id: int) -> Optional[dict]:
    with SessionLocal() as session:
        prompt = session.get(Prompt, prompt_id)
        if prompt is None:
            return None
        return _prompt_to_dict(prompt)


def create_prompt(title: str, summary: str, purpose: str, content: str) -> int:
    now = _utc_now_iso()
    with SessionLocal() as session:
        prompt = Prompt(
            title=title,
            summary=summary,
            purpose=purpose,
            content=content,
            created_at=now,
            updated_at=now,
        )
        session.add(prompt)
        session.commit()
        session.refresh(prompt)
        return prompt.id


def update_prompt(prompt_id: int, title: str, summary: str, purpose: str, content: str) -> None:
    now = _utc_now_iso()
    with SessionLocal() as session:
        prompt = session.get(Prompt, prompt_id)
        if prompt is None:
            return
        prompt.title = title
        prompt.summary = summary
        prompt.purpose = purpose
        prompt.content = content
        prompt.updated_at = now
        session.commit()


def delete_prompt(prompt_id: int) -> None:
    with SessionLocal() as session:
        prompt = session.get(Prompt, prompt_id)
        if prompt is None:
            return
        session.delete(prompt)
        session.commit()


def update_prompt_updated_at(prompt_id: int) -> None:
    now = _utc_now_iso()
    with SessionLocal() as session:
        prompt = session.get(Prompt, prompt_id)
        if prompt is None:
            return
        prompt.updated_at = now
        session.commit()


def list_tags() -> list[dict]:
    with SessionLocal() as session:
        tags = session.scalars(select(Tag).order_by(Tag.name.asc())).all()
        return [_tag_to_dict(tag) for tag in tags]


def get_tags_for_prompt(prompt_id: int) -> list[dict]:
    with SessionLocal() as session:
        stmt = (
            select(Tag)
            .join(Tag.prompts)
            .where(Prompt.id == prompt_id)
            .order_by(Tag.name.asc())
        )
        tags = session.scalars(stmt).all()
        return [_tag_to_dict(tag) for tag in tags]


def upsert_tag(name: str, color: str) -> int:
    with SessionLocal() as session:
        tag = session.scalar(select(Tag).where(Tag.name == name))
        if tag is not None:
            return tag.id
        tag = Tag(name=name, color=color)
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return tag.id


def update_tag_color(tag_id: int, color: str) -> None:
    with SessionLocal() as session:
        tag = session.get(Tag, tag_id)
        if tag is None:
            return
        tag.color = color
        session.commit()


def delete_tag(tag_id: int) -> None:
    with SessionLocal() as session:
        tag = session.get(Tag, tag_id)
        if tag is None:
            return
        session.delete(tag)
        session.commit()


def set_prompt_tags(prompt_id: int, tag_ids: Iterable[int]) -> None:
    normalized_tag_ids = list(dict.fromkeys(tag_ids))
    with SessionLocal() as session:
        prompt = session.get(Prompt, prompt_id)
        if prompt is None:
            return
        if normalized_tag_ids:
            tags = session.scalars(select(Tag).where(Tag.id.in_(normalized_tag_ids))).all()
            prompt.tags = list(tags)
        else:
            prompt.tags = []
        session.commit()


def list_prompts_with_tags(sort: str = "updated_desc", tag_id: Optional[int] = None) -> list[tuple[dict, list[dict]]]:
    order_by_map = {
        "updated_desc": Prompt.updated_at.desc(),
        "created_desc": Prompt.created_at.desc(),
    }
    order_by = order_by_map.get(sort, order_by_map["updated_desc"])

    with SessionLocal() as session:
        stmt = select(Prompt).options(selectinload(Prompt.tags))
        if tag_id is not None:
            stmt = stmt.join(Prompt.tags).where(Tag.id == tag_id).distinct()
        stmt = stmt.order_by(order_by)
        prompts = session.scalars(stmt).all()

        results: list[tuple[dict, list[dict]]] = []
        for prompt in prompts:
            prompt_dict = _prompt_to_dict(prompt)
            tags = sorted(prompt.tags, key=lambda tag: tag.name.lower())
            tag_dicts = [_tag_to_dict(tag) for tag in tags]
            results.append((prompt_dict, tag_dicts))
        return results
