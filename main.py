import os

from mcp.server.fastmcp import FastMCP
from pydantic import Field
from pypdf import PdfReader

mcp = FastMCP("ArticlesMCP", log_level="ERROR")

ARTICLES_DIR = os.path.realpath("/Users/none/ml-research-connector/articles")  # change to your folder
MAX_CHARS = 30000  # cap per article so long PDFs don't overflow the model's context


@mcp.tool(
    name="list_articles",
    description="List the filenames of all saved PDF articles in the articles directory."
)
def list_articles() -> list[str]:
    if not os.path.isdir(ARTICLES_DIR):
        raise ValueError(f"Articles directory not found: {ARTICLES_DIR}")

    return sorted(
        name
        for name in os.listdir(ARTICLES_DIR)
        if name.lower().endswith(".pdf")
        and os.path.isfile(os.path.join(ARTICLES_DIR, name))
    )


@mcp.tool(
    name="read_article",
    description="Extract and return the text of one PDF article by filename (from list_articles)."
)
def read_article(
    filename: str = Field(description="Filename of the PDF, e.g. 'my-article.pdf'"),
) -> str:
    path = os.path.realpath(os.path.join(ARTICLES_DIR, filename))

    # Block paths that escape the articles directory
    if os.path.commonpath([ARTICLES_DIR, path]) != ARTICLES_DIR:
        raise ValueError("Access outside the articles directory is not allowed")
    if not os.path.isfile(path):
        raise ValueError(f"Article not found: {filename}")

    reader = PdfReader(path)
    text = "\n\n".join((page.extract_text() or "") for page in reader.pages).strip()

    if not text:
        raise ValueError(
            f"No extractable text in {filename}. It may be a scanned PDF (images only)."
        )

    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "\n\n[Truncated: article continues beyond this point]"

    return text


@mcp.prompt(
    name="summarize_articles",
    description="Summarise every PDF article in the articles directory."
)
def summarize_articles() -> str:
    return (
        "Call list_articles to get all saved PDF articles. Then call read_article "
        "for each one, one at a time, and write a 2-3 sentence summary of each. "
        "Present the results as a list with the filename above each summary."
    )


if __name__ == "__main__":
    mcp.run()