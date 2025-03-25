from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from service.kana import  get_kana_data, get_kana_dict, search_words, get_words_by_slug, search_all_words

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# 添加自定义 zip 过滤器
templates.env.filters["zip"] = zip

@app.get("/intro")
def intro():
    return "intro"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, search: str = None):
    if search:
        words = search_words(search)
    else:
        words = None
    tables = await get_kana_data()
    kana_dict = get_kana_dict()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "tables": tables,
        "search": search,
        "words": words,
        "slugs": kana_dict
    })

@app.get("/kana/{slug}", response_class=HTMLResponse)
async def kana_detail(request: Request, slug: str):
    words, kana_dict, kana = get_words_by_slug(slug)
    return templates.TemplateResponse("kana.html", {
        "request": request,
        "kana": kana,
        "words": words,
        "slugs": kana_dict
    })

@app.get("/words", response_class=HTMLResponse)
async def words_page(request: Request):
    words = search_all_words()
    kana_dict = get_kana_dict()
    return templates.TemplateResponse("words.html", {"request": request, "words": words, "slugs": kana_dict})

@app.get("/grammar", response_class=HTMLResponse)
async def grammar_page(request: Request):
    return templates.TemplateResponse("grammar.html", {"request": request})

@app.get("/examples", response_class=HTMLResponse)
async def examples_page(request: Request):
    return templates.TemplateResponse("examples.html", {"request": request})