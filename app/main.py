from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import db

app = FastAPI(title="Prompt Collection")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/")
def index(request: Request):
    prompts = db.list_prompts_with_tags()
    return templates.TemplateResponse("index.html", {"request": request, "prompts": prompts})


@app.get("/prompts/new")
def new_prompt(request: Request):
    tags = db.list_tags()
    return templates.TemplateResponse("create.html", {"request": request, "tags": tags})


@app.post("/prompts")
def create_prompt(
    title: str = Form(...),
    summary: str = Form(...),
    purpose: str = Form(...),
    content: str = Form(...),
    tag_ids: list[str] = Form([]),
    new_tag_names: list[str] = Form([]),
    new_tag_colors: list[str] = Form([]),
):
    prompt_id = db.create_prompt(title=title, summary=summary, purpose=purpose, content=content)

    selected_tag_ids = [int(tid) for tid in tag_ids]

    for tag_name, tag_color in zip(new_tag_names, new_tag_colors):
        name = tag_name.strip()
        color = (tag_color or "#6b7280").strip()
        if not name:
            continue
        tag_id = db.upsert_tag(name, color)
        if tag_id not in selected_tag_ids:
            selected_tag_ids.append(tag_id)

    if selected_tag_ids:
        db.set_prompt_tags(prompt_id, selected_tag_ids)

    return RedirectResponse(url=f"/prompts/{prompt_id}", status_code=303)


@app.get("/prompts/{prompt_id}")
def prompt_detail(request: Request, prompt_id: int):
    prompt = db.get_prompt(prompt_id)
    if not prompt:
        return RedirectResponse(url="/", status_code=303)
    tags = db.get_tags_for_prompt(prompt_id)
    tag_ids = [int(tag["id"]) for tag in tags]
    all_tags = db.list_tags()
    created_date = str(prompt["created_at"]).split("T")[0]
    updated_date = str(prompt["updated_at"]).split("T")[0]
    return templates.TemplateResponse(
        "detail.html",
        {
            "request": request,
            "prompt": prompt,
            "tags": tags,
            "all_tags": all_tags,
            "tag_ids": tag_ids,
            "created_date": created_date,
            "updated_date": updated_date,
        },
    )

@app.get("/prompts/{prompt_id}/edit")
def edit_prompt(request: Request, prompt_id: int):
    prompt = db.get_prompt(prompt_id)
    if not prompt:
        return RedirectResponse(url="/", status_code=303)
    tags = db.get_tags_for_prompt(prompt_id)
    tag_ids = [int(tag["id"]) for tag in tags]
    all_tags = db.list_tags()
    return templates.TemplateResponse(
        "edit.html",
        {"request": request, "prompt": prompt, "all_tags": all_tags, "tag_ids": tag_ids},
    )


@app.post("/prompts/{prompt_id}")
def update_prompt(
    prompt_id: int,
    title: str = Form(...),
    summary: str = Form(...),
    purpose: str = Form(...),
    content: str = Form(...),
    tag_ids: list[str] = Form([]),
    new_tag_names: list[str] = Form([]),
    new_tag_colors: list[str] = Form([]),
):
    db.update_prompt(prompt_id, title=title, summary=summary, purpose=purpose, content=content)

    selected_tag_ids = [int(tid) for tid in tag_ids]
    for tag_name, tag_color in zip(new_tag_names, new_tag_colors):
        name = tag_name.strip()
        color = (tag_color or "#6b7280").strip()
        if not name:
            continue
        tag_id = db.upsert_tag(name, color)
        if tag_id not in selected_tag_ids:
            selected_tag_ids.append(tag_id)

    db.set_prompt_tags(prompt_id, selected_tag_ids)
    return RedirectResponse(url=f"/prompts/{prompt_id}", status_code=303)


@app.post("/prompts/{prompt_id}/delete")
def delete_prompt(prompt_id: int):
    db.delete_prompt(prompt_id)
    return RedirectResponse(url="/", status_code=303)


@app.get("/tags")
def manage_tags(request: Request):
    tags = db.list_tags()
    return templates.TemplateResponse("tags.html", {"request": request, "tags": tags})


@app.post("/tags")
def create_tag(name: str = Form(...), color: str = Form("#6b7280")):
    db.upsert_tag(name.strip(), color)
    return RedirectResponse(url="/tags", status_code=303)


@app.post("/tags/{tag_id}/delete")
def remove_tag(tag_id: int):
    db.delete_tag(tag_id)
    return RedirectResponse(url="/tags", status_code=303)


@app.post("/tags/{tag_id}/update")
def update_tag(tag_id: int, color: str = Form("#6b7280")):
    db.update_tag_color(tag_id, color)
    return RedirectResponse(url="/tags", status_code=303)
