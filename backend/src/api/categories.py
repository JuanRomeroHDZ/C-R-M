from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status
from src.db.connection import get_db_connection, execute_query
from src.models.schemas import CategoryCreate, CategoryUpdate, CategoryOut

router = APIRouter(prefix="/api/v1/extraction/categories", tags=["Categories"])


def _hydrate_category(cat_row: Dict[str, Any]) -> CategoryOut:
    cat_id = cat_row["id"]
    kw_rows = execute_query("SELECT keyword FROM category_keywords WHERE category_id = %s;", (cat_id,))
    keywords = [r["keyword"] for r in kw_rows]

    osm_rows = execute_query("SELECT key, value FROM category_osm_tags WHERE category_id = %s;", (cat_id,))
    osm_tags = [{"key": r["key"], "value": r["value"]} for r in osm_rows]

    return CategoryOut(
        id=cat_row["id"],
        slug=cat_row["slug"],
        name=cat_row["name"],
        is_active=cat_row["is_active"],
        created_at=cat_row["created_at"],
        updated_at=cat_row["updated_at"],
        keywords=keywords,
        osm_tags=osm_tags
    )


@router.get("", response_model=List[CategoryOut])
def list_categories(active_only: bool = False):
    query = "SELECT id, slug, name, is_active, created_at, updated_at FROM categories"
    if active_only:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY name ASC;"

    rows = execute_query(query)
    return [_hydrate_category(r) for r in rows]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate):
    existing = execute_query("SELECT id FROM categories WHERE slug = %s;", (payload.slug,))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with slug '{payload.slug}' already exists."
        )

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO categories (slug, name, is_active)
                VALUES (%s, %s, %s)
                RETURNING id, slug, name, is_active, created_at, updated_at;
                """,
                (payload.slug, payload.name, payload.is_active)
            )
            cat_row = cur.fetchone()
            cat_id = cat_row["id"]

            for kw in payload.keywords:
                cur.execute(
                    "INSERT INTO category_keywords (category_id, keyword) VALUES (%s, %s);",
                    (cat_id, kw.strip())
                )

            for tag in payload.osm_tags:
                cur.execute(
                    "INSERT INTO category_osm_tags (category_id, key, value) VALUES (%s, %s, %s);",
                    (cat_id, tag["key"].strip(), tag["value"].strip())
                )

    return _hydrate_category(cat_row)


@router.get("/{slug_or_id}", response_model=CategoryOut)
def get_category(slug_or_id: str):
    rows = execute_query(
        "SELECT id, slug, name, is_active, created_at, updated_at FROM categories WHERE slug = %s OR id::text = %s;",
        (slug_or_id, slug_or_id)
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return _hydrate_category(rows[0])


@router.put("/{slug_or_id}", response_model=CategoryOut)
def update_category(slug_or_id: str, payload: CategoryUpdate):
    rows = execute_query(
        "SELECT id FROM categories WHERE slug = %s OR id::text = %s;",
        (slug_or_id, slug_or_id)
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    cat_id = rows[0]["id"]

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if payload.name is not None or payload.is_active is not None:
                updates = []
                params = []
                if payload.name is not None:
                    updates.append("name = %s")
                    params.append(payload.name)
                if payload.is_active is not None:
                    updates.append("is_active = %s")
                    params.append(payload.is_active)
                updates.append("updated_at = NOW()")
                params.append(cat_id)

                sql = f"UPDATE categories SET {', '.join(updates)} WHERE id = %s;"
                cur.execute(sql, tuple(params))

            if payload.keywords is not None:
                cur.execute("DELETE FROM category_keywords WHERE category_id = %s;", (cat_id,))
                for kw in payload.keywords:
                    cur.execute(
                        "INSERT INTO category_keywords (category_id, keyword) VALUES (%s, %s);",
                        (cat_id, kw.strip())
                    )

            if payload.osm_tags is not None:
                cur.execute("DELETE FROM category_osm_tags WHERE category_id = %s;", (cat_id,))
                for tag in payload.osm_tags:
                    cur.execute(
                        "INSERT INTO category_osm_tags (category_id, key, value) VALUES (%s, %s, %s);",
                        (cat_id, tag["key"].strip(), tag["value"].strip())
                    )

    updated_rows = execute_query(
        "SELECT id, slug, name, is_active, created_at, updated_at FROM categories WHERE id = %s;",
        (cat_id,)
    )
    return _hydrate_category(updated_rows[0])


@router.delete("/{slug_or_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(slug_or_id: str, hard_delete: bool = False):
    rows = execute_query(
        "SELECT id FROM categories WHERE slug = %s OR id::text = %s;",
        (slug_or_id, slug_or_id)
    )
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")

    cat_id = rows[0]["id"]
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            if hard_delete:
                cur.execute("DELETE FROM categories WHERE id = %s;", (cat_id,))
            else:
                cur.execute("UPDATE categories SET is_active = FALSE, updated_at = NOW() WHERE id = %s;", (cat_id,))
