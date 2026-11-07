# ml-research-connector

A small [MCP](https://modelcontextprotocol.io) server that gives Claude access to a local folder of PDF research papers. Claude can list the papers you have saved and read their text, so you can ask for summaries, comparisons, and literature reviews grounded in your own library.

Built with [FastMCP](https://github.com/modelcontextprotocol/python-sdk) and managed with [uv](https://docs.astral.sh/uv/).

## Features

| Type   | Name                 | Description                                                         |
| ------ | -------------------- | ------------------------------------------------------------------- |
| Tool   | `list_articles`      | Returns the filenames of all PDFs in the articles directory.        |
| Tool   | `read_article`       | Extracts the text of one PDF by filename (capped at 30,000 chars).  |
| Prompt | `summarize_articles` | Summarizes every saved article in 2-3 sentences each.               |

Built-in safeguards:

- **Path traversal protection.** `read_article` rejects any filename that resolves outside the articles directory.
- **Context-window cap.** Long papers are truncated at `MAX_CHARS` and marked with `[Truncated: ...]`.
- **Clear errors** for missing folders, missing files, and scanned PDFs with no extractable text.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Python 3.10+ (uv installs this for you if needed)
- Claude Desktop and/or Claude Code
- macOS, Linux, or Windows

## Project structure

```
ml-research-connector/
├── main.py            # the MCP server
├── pyproject.toml     # dependencies, managed by uv
├── articles/          # put your PDFs here
└── README.md
```

## Setup

> **A note on paths.** Your clone will live somewhere different from anyone else's, so this guide uses `/absolute/path/to/ml-research-connector` as a placeholder. Wherever you see it, substitute the real location. To get it, run `pwd` (macOS/Linux) or `cd` (Windows) from inside the cloned folder.

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/ml-research-connector.git
cd ml-research-connector
```

### 2. Install dependencies

```bash
uv sync
```

This creates a `.venv` inside the project and installs everything from `pyproject.toml`.

### 3. Add your PDFs

The server reads from the `articles/` folder inside the project by default. Create it and add your papers:

```bash
mkdir -p articles
cp ~/Downloads/*.pdf articles/
```

To use a different folder, set the `ARTICLES_DIR` environment variable (see [Configuration](#configuration)).

### 4. Test the server

```bash
uv run main.py
```

A working stdio server starts and then waits silently for input. Press `Ctrl+C` to stop it. Any traceback means something is wrong with the script or its dependencies.

### 5. Register it with your client

#### Claude Code

Run this from inside the cloned folder so `$(pwd)` expands to the correct path:

```bash
claude mcp add ml-research-connector --scope user -- uv --directory "$(pwd)" run main.py
```

`--scope user` makes the server available from every directory. Without it, the server is tied to the folder you ran the command in.

Verify:

```bash
claude mcp list
```

Inside a session, `/mcp` shows connection status and tools.

#### Claude Desktop

Open **Settings → Developer → Edit Config**, or edit the file directly:

| OS      | Config file                                                       |
| ------- | ----------------------------------------------------------------- |
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json`                     |

Add the server to the `mcpServers` block, keeping any other settings already in the file:

```json
{
  "mcpServers": {
    "ml-research-connector": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/ml-research-connector",
        "run",
        "main.py"
      ]
    }
  }
}
```

Desktop needs a full absolute path here. It does not expand `~` or `$(pwd)`, and it does not use your shell's `PATH`. If Desktop reports `spawn uv ENOENT`, replace `"uv"` with the absolute path from `which uv` (macOS/Linux) or `where uv` (Windows).

### 6. Restart the client

Servers are loaded at startup, so changes to the config or to `main.py` only take effect after a full restart:

- **Claude Desktop:** quit fully (Cmd+Q on macOS, or right-click the tray icon and choose Quit on Windows), then reopen. Closing the window is not enough.
- **Claude Code:** exit with `/exit` and start a new `claude` session.

## Usage

Name the connector in your prompt so Claude calls the tools instead of answering from memory.

**Quick test**

```
Use ml-research-connector to list all saved articles.
```

**Summarize one paper**

```
Use ml-research-connector to list my articles, then read the one about [topic]
and summarize it: the problem, method, key results, and limitations.
```

**Compare papers**

```
List my saved articles with ml-research-connector, read all of them, and give me
a comparison table: task, method, dataset, headline results, and weaknesses.
```

**Literature review**

```
Using ml-research-connector, read every article in my library and write a short
literature review grouped by theme. Cite each claim by filename and flag where
papers disagree.
```

**Targeted extraction**

```
Read [filename].pdf with ml-research-connector and extract the experimental
setup: datasets, baselines, hyperparameters, and evaluation metrics.
```

You can also run the built-in `summarize_articles` prompt from clients that expose MCP prompts.

**Tips**

- Ask for citations by filename so you can check claims against the source.
- With many long PDFs, read a few at a time. Reading everything in one go can overflow the context window.
- Each article is capped at 30,000 characters, so very long papers are cut off. Ask for specific sections or raise `MAX_CHARS` if you need more.

## Configuration

Settings live at the top of `main.py`:

```python
ARTICLES_DIR = os.path.realpath(
    os.environ.get(
        "ARTICLES_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles"),
    )
)
MAX_CHARS = 30000
```

| Setting        | Default                          | Purpose                                  |
| -------------- | -------------------------------- | ---------------------------------------- |
| `ARTICLES_DIR` | `articles/` next to `main.py`    | Folder the server reads PDFs from.       |
| `MAX_CHARS`    | `30000`                          | Maximum characters returned per article. |

### Using a different PDF folder

Pass `ARTICLES_DIR` through the client config.

**Claude Desktop**

```json
"ml-research-connector": {
  "command": "uv",
  "args": ["--directory", "/absolute/path/to/ml-research-connector", "run", "main.py"],
  "env": { "ARTICLES_DIR": "/absolute/path/to/your/pdfs" }
}
```

**Claude Code**

```bash
claude mcp add ml-research-connector --scope user \
  -e ARTICLES_DIR=/absolute/path/to/your/pdfs \
  -- uv --directory "$(pwd)" run main.py
```

## Troubleshooting

**The server doesn't appear in the client**

- Claude Code and Claude Desktop use separate configs. `claude mcp add` only affects Claude Code, so Desktop needs its own entry in `claude_desktop_config.json`.
- Fully quit and relaunch the client after any change. A session that was open before you added the server will not show it.
- Check the Desktop config for JSON syntax errors such as a missing comma. Invalid JSON makes Desktop ignore the file.
- Make sure the `--directory` path is absolute and points at your clone.
- claude.ai in the browser cannot use local stdio servers at all.
- If `claude mcp list` shows the server as connected but a session says "No servers added", you are probably looking at a different surface (an IDE extension or Desktop chat) than the terminal. Test in a plain terminal with `claude`.

**`spawn uv ENOENT` in the Desktop logs**

- Desktop can't find `uv`. Use the absolute path from `which uv` (or `where uv` on Windows) as the `command`.

**`Articles directory not found: ...`**

- Create the folder named in the error, or set `ARTICLES_DIR` to the right location.
- If the path in the error differs from what your config and `main.py` say, an old process or another copy of the script is running. Stop it and relaunch:

  ```bash
  pkill -f main.py
  ```

  Then quit the client completely and reopen it.
- Look for stray copies of the script:

  ```bash
  find ~ -name main.py -not -path "*/.venv/*"
  ```

**`No extractable text in <file>`**

- The PDF is probably a scan (images only). Run OCR on it first, for example with `ocrmypdf`.

**Article text ends with `[Truncated...]`**

- Output is capped at `MAX_CHARS` to protect the context window. Raise the value in `main.py` if needed.

**The server connects but tools fail, or the protocol breaks**

- Don't `print()` to stdout in `main.py`. Stdout carries the MCP protocol, so stray output corrupts it. Log to stderr instead:

  ```python
  import sys
  print("debug message", file=sys.stderr)
  ```

**Where to find logs**

- Claude Desktop (macOS):

  ```bash
  tail -n 50 ~/Library/Logs/Claude/mcp-server-ml-research-connector.log
  ```

  On Windows, look in `%APPDATA%\Claude\logs\`.
- Claude Code: `claude mcp list` shows status, and `/mcp` inside a session shows tools.
- Run the server by hand to see startup errors: `uv run main.py`

## Removing the server

```bash
# Claude Code
claude mcp remove ml-research-connector -s user
```

For Claude Desktop, delete the `ml-research-connector` entry from `claude_desktop_config.json` and restart.

## Security notes

- The server is read-only and only serves `.pdf` files from `ARTICLES_DIR`.
- Filenames are resolved with `os.path.realpath` and checked against the articles directory, which blocks `../` traversal and symlinks that point outside it.
- Text from PDFs is passed to the model as-is. Treat papers from untrusted sources with the same care as any other untrusted input.

## Contributing

Issues and pull requests are welcome. Please don't commit copyrighted PDFs. Add `articles/*.pdf` to your `.gitignore` and keep an empty `articles/.gitkeep` so the folder exists after cloning.