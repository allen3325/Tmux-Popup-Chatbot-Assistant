# Tmux Popup Chatbot Assistant

This is a lightweight AI assistant designed for Tmux users. It leverages Tmux's `display-popup` feature to let you summon an LLM with a hotkey for code lookups, debugging, or concept explanations — all without leaving your terminal session.

## Features

- **Fast responses:** Uses Google's latest `gemini-flash-lite-latest` model.
- **Streaming output:** Responses appear with a typewriter-style streaming effect, so you don't have to wait for the entire answer.
- **Nice rendering:** Uses `rich` to render Markdown with syntax-highlighted code blocks and good formatting.
- **Secure by design:** API keys are stored locally in a `.env` file to avoid accidentally committing them or polluting global environment variables.
- **Conversation memory:** As long as the Tmux session remains active, closing and reopening the popup preserves the chat history.

## Directory Layout

Recommended location for the scripts is `~/scripts`:

```text
~/scripts/
├── .venv/
├── .env                 # (create this yourself) stores the API key
└── gemini_popup.py      # main Python script
```

## Installation

### 1. Prepare the environment

Clone the repository and set up a Python virtual environment:

```bash
git clone https://github.com/allen3325/Tmux-Popup-Chatbot-Assistant.git
cd Tmux-Popup-Chatbot-Assistant
uv sync
```

### 2. Set your API key

Get a Google Gemini API key (see https://aistudio.google.com/) and create a `.env` file in `~/scripts/`:

```bash
# ~/scripts/.env
GEMINI_API_KEY="YOUR_API_KEY_STARTING_WITH_AIza_..."
```

## Tmux Configuration

Add the following to your `~/.tmux.conf`.

This configuration ensures:

1. The popup is triggered with **Prefix + Alt-c**.
2. If a session named `popup_gemini` exists it will attach (preserving state); otherwise it creates a new session (starting a new conversation).
3. The script runs using the Python interpreter from the virtual environment.

```tmux
bind M-c display-popup -E -w 80% -h 80% "tmux attach -t popup_gemini || tmux new -s popup_gemini '~/Tmux-Popup-Chatbot-Assistant/.venv/bin/python ~/Tmux-Popup-Chatbot-Assistant/gemini_popup.py'"
```

If you prefer invoking the popup directly with `Alt-c` (without the tmux prefix), add `-n` after `bind`.

**Apply the config:**

```bash
tmux source ~/.tmux.conf
```

## How to Use

1. In Tmux press **Prefix + Alt + c** (commonly `Ctrl+b`, then `Alt+c`).
2. Type your question.
3. Press `Esc` or type `exit` to close the popup (the session remains running in the background).
4. To fully terminate the program, type `q` in the popup or press `Ctrl+c`.
