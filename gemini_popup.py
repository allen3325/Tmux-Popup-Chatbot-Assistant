import os
import sys
from google import genai
from google.genai import types
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.live import Live
from dotenv import load_dotenv

# 1. Initialization settings
script_dir = os.path.dirname(os.path.abspath(__file__))
# Compose the full path to .env
env_path = os.path.join(script_dir, '.env')

# Load environment variables
load_dotenv(env_path)

# Read the Key
API_KEY = os.environ.get("GEMINI_API_KEY")

if not API_KEY:
    # You can use rich to print a prettier error, but print also works
    print(f"Error: GEMINI_API_KEY not found in {env_path}")
    sys.exit(1)

# Initialize Rich Console
console = Console()

# 2. Initialize Gemini Client (using the latest google-genai SDK)
client = genai.Client(api_key=API_KEY)

# Set the default model
DEFAULT_MODEL_ID = "gemini-flash-lite-latest"

def get_available_models():
    """Get list of models that support generateContent"""
    models = []
    for m in client.models.list():
        if m.supported_actions:
            for action in m.supported_actions:
                if action == "generateContent":
                    models.append(m.name)
                    break
    return models

def select_model(current_model):
    """Let user select a model from available models"""
    console.print("\n[bold yellow]Fetching available models...[/bold yellow]")
    models = get_available_models()
    
    if not models:
        console.print("[bold red]No available models found[/bold red]")
        return current_model
    
    console.print("\n[bold cyan]Available models:[/bold cyan]")
    for i, model in enumerate(models, 1):
        marker = " [green](current)[/green]" if model == current_model else ""
        console.print(f"  [yellow]{i}.[/yellow] {model}{marker}")
    
    console.print(f"\nEnter a number to select a model, or press Enter to cancel")
    
    try:
        choice = console.input("[bold green]Select > [/bold green]")
        if not choice.strip():
            return current_model
        
        idx = int(choice) - 1
        if 0 <= idx < len(models):
            selected = models[idx]
            console.print(f"[bold green]Switched to model: {selected}[/bold green]")
            return selected
        else:
            console.print("[bold red]Invalid selection[/bold red]")
            return current_model
    except ValueError:
        console.print("[bold red]Please enter a valid number[/bold red]")
        return current_model

def main():
    console.clear()
    
    # Track current model
    current_model = DEFAULT_MODEL_ID
    
    # Display welcome panel
    console.print(Panel.fit(
        f"[bold cyan]Quick Chatbot Assistant[/bold cyan]\n"
        f"Model: {current_model}\n"
        "Type '/model' to select a model\n"
        "Type 'q' or 'exit' to quit", 
        border_style="blue"
    ))

    # 3. Create chat session (this preserves context for follow-up questions)
    chat = client.chats.create(model=current_model)

    while True:
        try:
            # Get user input
            user_input = console.input("\n[bold green]You > [/bold green]")
            
            if user_input.lower() in ['q', 'exit', 'quit']:
                break
            if not user_input.strip():
                continue
            
            # Handle /model command
            if user_input.lower() == '/model':
                new_model = select_model(current_model)
                if new_model != current_model:
                    current_model = new_model
                    # Recreate chat session with new model
                    chat = client.chats.create(model=current_model)
                    console.print(f"[bold cyan]New chat session created (Model: {current_model})[/bold cyan]")
                continue

            # Prepare variable to receive response
            full_response_text = ""
            
            # Create a panel to show that this reply is from Gemini
            with Live(
                Panel("...", title="Gemini", border_style="magenta", expand=False), 
                refresh_per_second=12
            ) as live:
                
                # 4. Call API (Streaming mode)
                # config parameter is optional, default is plain text
                response_stream = chat.send_message_stream(
                    message=user_input,
                    config=types.GenerateContentConfig(
                        temperature=1.0,
                    )
                )

                for chunk in response_stream:
                    if chunk.text:
                        full_response_text += chunk.text
                        # Update panel content in real-time and render Markdown
                        live.update(
                            Panel(
                                Markdown(full_response_text), 
                                title="Gemini", 
                                border_style="magenta",
                                expand=False
                            )
                        )

        except KeyboardInterrupt:
            # Allow quick exit with Ctrl+C
            break
        except Exception as e:
            console.print(f"\n[bold red]Error: {e}[/bold red]")
            # If it's an API Error, the output is usually clear

if __name__ == "__main__":
    main()