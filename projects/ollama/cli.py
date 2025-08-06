#!/usr/bin/env python3

import click
import os
from agent import LocalAgent
import json


@click.group()
@click.option('--model', default='llama3.2:1b', help='Ollama model to use')
@click.option('--host', default='http://localhost:11434', help='Ollama host URL')
@click.option('--warmup/--no-warmup', default=True, help='Auto-warmup model on first use')
@click.pass_context
def cli(ctx, model, host, warmup):
    """Local AI Agent powered by Ollama"""
    ctx.ensure_object(dict)
    ctx.obj['model'] = model
    ctx.obj['host'] = host
    ctx.obj['warmup'] = warmup


@cli.command()
@click.option('--system', '-s', help='Set system prompt')
@click.option('--warmup/--no-warmup', default=None, help='Override global warmup setting')
@click.pass_context
def chat(ctx, system, warmup):
    """Start interactive chat with the agent"""
    use_warmup = warmup if warmup is not None else ctx.obj['warmup']
    agent = LocalAgent(model=ctx.obj['model'], host=ctx.obj['host'], auto_warmup=use_warmup)
    
    if not agent.is_ollama_running():
        click.echo(click.style("Error: Ollama is not running. Please start Ollama service first.", fg='red'))
        return
    
    if system:
        agent.set_system_prompt(system)
    
    available_models = agent.get_available_models()
    if ctx.obj['model'].split(':')[0] not in [m.split(':')[0] for m in available_models]:
        click.echo(click.style(f"Warning: Model {ctx.obj['model']} may not be available.", fg='yellow'))
    
    click.echo(click.style(f"🤖 Local Agent initialized with {ctx.obj['model']}", fg='green'))
    click.echo(click.style("Commands: /quit, /reset, /help, /save, /load, /warmup", fg='blue'))
    click.echo()
    
    while True:
        user_input = click.prompt("You", prompt_suffix=" ").strip()
        
        if user_input.startswith('/'):
            if user_input in ['/quit', '/exit']:
                break
            elif user_input == '/reset':
                agent.reset_conversation()
                click.echo(click.style("Conversation reset.", fg='yellow'))
                continue
            elif user_input == '/help':
                click.echo("Commands:")
                click.echo("  /quit, /exit - Exit the program")
                click.echo("  /reset - Clear conversation history")
                click.echo("  /help - Show this help")
                click.echo("  /save <filename> - Save conversation")
                click.echo("  /load <filename> - Load conversation")
                click.echo("  /warmup - Manually warm up the model")
                continue
            elif user_input.startswith('/save'):
                parts = user_input.split(' ', 1)
                filename = parts[1] if len(parts) > 1 else 'conversation.json'
                save_conversation(agent, filename)
                continue
            elif user_input.startswith('/load'):
                parts = user_input.split(' ', 1)
                filename = parts[1] if len(parts) > 1 else 'conversation.json'
                load_conversation(agent, filename)
                continue
            elif user_input == '/warmup':
                if agent.is_warmed_up():
                    click.echo(click.style("Model is already warmed up", fg='green'))
                else:
                    agent.warmup()
                continue
        
        if not user_input:
            continue
        
        with click.progressbar(length=1, label='Thinking') as bar:
            response = agent.chat(user_input)
            bar.update(1)
        
        click.echo(click.style("Assistant: ", fg='green') + response)
        click.echo()


@cli.command()
@click.argument('prompt')
@click.option('--system', '-s', help='Set system prompt')
@click.option('--warmup/--no-warmup', default=None, help='Override global warmup setting')
@click.pass_context
def ask(ctx, prompt, system, warmup):
    """Ask a single question to the agent"""
    use_warmup = warmup if warmup is not None else ctx.obj['warmup']
    agent = LocalAgent(model=ctx.obj['model'], host=ctx.obj['host'], auto_warmup=use_warmup)
    
    if not agent.is_ollama_running():
        click.echo(click.style("Error: Ollama is not running.", fg='red'))
        return
    
    if system:
        agent.set_system_prompt(system)
    
    response = agent.chat(prompt)
    click.echo(response)


@cli.command()
@click.pass_context
def models(ctx):
    """List available models"""
    agent = LocalAgent(host=ctx.obj['host'])
    
    if not agent.is_ollama_running():
        click.echo(click.style("Error: Ollama is not running.", fg='red'))
        return
    
    available_models = agent.get_available_models()
    click.echo("Available models:")
    for model in available_models:
        marker = " ✓" if model == ctx.obj['model'] else ""
        click.echo(f"  {model}{marker}")


@cli.command()
@click.pass_context
def warmup(ctx):
    """Warm up the specified model for faster responses"""
    agent = LocalAgent(model=ctx.obj['model'], host=ctx.obj['host'])
    
    if not agent.is_ollama_running():
        click.echo(click.style("Error: Ollama is not running.", fg='red'))
        return
    
    if agent.is_warmed_up():
        click.echo(click.style(f"Model {ctx.obj['model']} is already warmed up!", fg='green'))
    else:
        success = agent.warmup()
        if success:
            click.echo(click.style(f"Model {ctx.obj['model']} is now ready for fast responses!", fg='green'))
        else:
            click.echo(click.style("Warmup failed. Check if the model is available.", fg='red'))


@cli.command()
@click.pass_context
def status(ctx):
    """Check system status"""
    agent = LocalAgent(host=ctx.obj['host'])
    
    if agent.is_ollama_running():
        click.echo(click.style("✓ Ollama is running", fg='green'))
        models = agent.get_available_models()
        click.echo(f"Available models: {len(models)}")
        
        # Check if the current model is warmed up
        test_agent = LocalAgent(model=ctx.obj['model'], host=ctx.obj['host'])
        if test_agent.is_warmed_up():
            click.echo(click.style(f"✓ Model {ctx.obj['model']} is warmed up", fg='green'))
        else:
            click.echo(click.style(f"○ Model {ctx.obj['model']} is cold (use 'warmup' command)", fg='yellow'))
    else:
        click.echo(click.style("✗ Ollama is not running", fg='red'))


def save_conversation(agent: LocalAgent, filename: str):
    """Save conversation to file"""
    try:
        history = agent.get_conversation_history()
        data = [{"role": msg.role, "content": msg.content, "timestamp": msg.timestamp} 
                for msg in history]
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        click.echo(click.style(f"Conversation saved to {filename}", fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error saving conversation: {e}", fg='red'))


def load_conversation(agent: LocalAgent, filename: str):
    """Load conversation from file"""
    try:
        if not os.path.exists(filename):
            click.echo(click.style(f"File {filename} not found", fg='red'))
            return
        
        with open(filename, 'r') as f:
            data = json.load(f)
        
        agent.reset_conversation()
        for item in data:
            agent.conversation.add_message(item['role'], item['content'])
        
        click.echo(click.style(f"Conversation loaded from {filename}", fg='green'))
    except Exception as e:
        click.echo(click.style(f"Error loading conversation: {e}", fg='red'))


if __name__ == '__main__':
    cli()