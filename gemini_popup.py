import os
import sys
from google import genai
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule
from rich.theme import Theme
from rich.padding import Padding
from dotenv import load_dotenv

# Import prompt_toolkit for input handling
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style as PromptStyle
from prompt_toolkit.formatted_text import HTML

# 1. Initialization
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
load_dotenv(env_path)

API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    print(f"Error: GEMINI_API_KEY not found in {env_path}")
    sys.exit(1)

# Custom theme for Rich
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red"
})
console = Console(theme=custom_theme)

# 2. Gemini Client
client = genai.Client(api_key=API_KEY)
DEFAULT_MODEL_ID = "gemini-2.0-flash-lite-preview-02-05"

# 3. Prompt Toolkit Setup
session = PromptSession(history=InMemoryHistory())
prompt_style = PromptStyle.from_dict({
    'prompt': 'bold #00ff00',  # Green color
    'input': '#ffffff',         # White input
})

def get_available_models():
    """Fetch available models safely."""
    models = []
    try:
        for m in client.models.list():
            if m.supported_actions and "generateContent" in m.supported_actions:
                models.append(m.name)
    except Exception as e:
        console.print(f"[danger]Error fetching models: {e}[/danger]")
    return models

def select_model(current_model):
    """Model selection UI."""
    console.print("\n[info]Fetching available models...[/info]")
    models = get_available_models()
    
    if not models:
        console.print("[danger]No available models found[/danger]")
        return current_model
    
    console.print("\n[bold cyan]Available models:[/bold cyan]")
    for i, model in enumerate(models, 1):
        marker = " [green](current)[/green]" if model == current_model else ""
        console.print(f"  [yellow]{i}.[/yellow] {model}{marker}")
    
    console.print(f"\nEnter number to select, or Enter to keep current.")
    
    try:
        choice = session.prompt(HTML('<b><style color="green">Select &gt; </style></b>'), style=prompt_style)
        if not choice.strip():
            return current_model
        
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            selected = models[idx]
            console.print(f"[bold green]Switched to: {selected}[/bold green]")
            return selected
        else:
            console.print("[danger]Invalid selection[/danger]")
            return current_model
    except ValueError:
        return current_model

def stream_response(chat, user_input, console):
    """
    Handles the streaming response directly to stdout for maximum smoothness.
    Returns the full text for post-processing.
    """
    full_text = ""
    
    # 這裡我們只印出一個簡單的標題，告訴使用者開始生成了
    console.print(Rule(title="[dim]Streaming[/dim]", style="dim blue"), style="blue")
    
    try:
        response_stream = chat.send_message_stream(
            message=user_input,
            config=types.GenerateContentConfig(
                temperature=0.7,
            )
        )

        # DIRECT STREAMING LOOP (Raw Text)
        for chunk in response_stream:
            if chunk.text:
                sys.stdout.write(chunk.text)
                sys.stdout.flush()
                full_text += chunk.text

        sys.stdout.write("\n")
        
    except Exception as e:
        console.print(f"\n[danger]Stream Error: {e}[/danger]")
    
    return full_text

def main():
    console.clear()
    current_model = DEFAULT_MODEL_ID
    
    console.print(Panel.fit(
        f"[bold cyan]Smooth Chatbot Assistant[/bold cyan]\n"
        f"Model: {current_model}\n"
        "Features: Fast Stream -> Markdown Render\n"
        "Type '/model' to select model, 'q' to quit", 
        border_style="blue"
    ))

    chat = client.chats.create(model=current_model)

    while True:
        try:
            # 1. Get Input
            user_input = session.prompt(HTML('\n<b><style color="green">You &gt; </style></b>'), style=prompt_style)
            
            if user_input.lower() in ['q', 'exit', 'quit']:
                break
            if not user_input.strip():
                continue
            
            # 2. Handle Commands
            if user_input.lower() == '/model':
                new_model = select_model(current_model)
                if new_model != current_model:
                    current_model = new_model
                    chat = client.chats.create(model=current_model)
                continue

            # 3. Stream Response (Raw Text for Speed)
            full_response = stream_response(chat, user_input, console)
            
            # 4. Final Markdown Rendering (Pretty Output)
            # 這是你要求開啟的部分：生成結束後，顯示漂亮的 Markdown 面板
            if full_response:
                console.print(Rule(title="[bold magenta]Final Output[/bold magenta]", style="magenta"))
                console.print(Padding(Markdown(full_response), (1, 2)))
                console.print(Rule(style="dim magenta"))

        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type 'q' to quit.[/yellow]")
            continue
        except Exception as e:
            console.print(f"\n[danger]System Error: {e}[/danger]")

if __name__ == "__main__":
    main()