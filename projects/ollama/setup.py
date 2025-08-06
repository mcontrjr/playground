#!/usr/bin/env python3

"""
Setup script for Local AI Agent
"""

import subprocess
import sys
import os
import time


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is supported"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ required. Current version:", sys.version)
        return False
    print(f"✅ Python {version.major}.{version.minor} supported")
    return True


def install_requirements():
    """Install Python requirements"""
    if os.path.exists("requirements.txt"):
        return run_command("pip install -r requirements.txt", "Installing Python requirements")
    else:
        print("⚠️  requirements.txt not found")
        return False


def check_ollama():
    """Check if Ollama is installed and running"""
    # Check if ollama command exists
    if not run_command("which ollama", "Checking Ollama installation"):
        print("❌ Ollama not found. Please install Ollama first:")
        print("   curl -fsSL https://ollama.com/install.sh | sh")
        return False
    
    # Check if Ollama is running
    if not run_command("curl -s http://localhost:11434/api/tags > /dev/null", "Checking Ollama service"):
        print("⚠️  Ollama is not running. Start it with: ollama serve")
        print("   Or run: systemctl start ollama (if using systemd)")
        return False
    
    return True


def check_model():
    """Check if llama3.2:1b model is available"""
    return run_command("ollama list | grep llama3.2:1b", "Checking for llama3.2:1b model")


def warmup_model():
    """Warm up the llama3.2:1b model for immediate responsiveness"""
    print("🔥 Warming up llama3.2:1b model for fast responses...")
    try:
        # Import and use the agent to warm up
        from agent import LocalAgent
        agent = LocalAgent(model="llama3.2:1b")
        
        if agent.is_ollama_running():
            success = agent.warmup(show_progress=True)
            if success:
                print("✅ Model is now warmed up and ready for fast responses!")
                return True
            else:
                print("⚠️  Model warmup failed, but the agent should still work (just slower on first request)")
        else:
            print("❌ Cannot warm up: Ollama is not running")
            
    except Exception as e:
        print(f"⚠️  Warmup failed: {e}")
        print("   The agent should still work, just slower on first request")
    
    return False


def setup_env_file():
    """Create .env file from example"""
    if not os.path.exists(".env") and os.path.exists(".env.example"):
        run_command("cp .env.example .env", "Creating .env file from example")
        print("✅ You can customize .env file for your configuration")
    elif os.path.exists(".env"):
        print("✅ .env file already exists")


def main():
    print("🚀 Local AI Agent Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Install requirements
    if not install_requirements():
        print("⚠️  Failed to install requirements. Try manually: pip install -r requirements.txt")
    
    # Check Ollama
    ollama_running = check_ollama()
    model_available = False
    
    if ollama_running:
        print("✅ Ollama is running")
        
        # Check model
        model_available = check_model()
        if model_available:
            print("✅ llama3.2:1b model is available")
        else:
            print("⚠️  llama3.2:1b model not found. Pull it with:")
            print("   ollama pull llama3.2:1b")
    
    # Setup environment file
    setup_env_file()
    
    # Warm up model if everything is ready
    if ollama_running and model_available:
        print("\n" + "=" * 50)
        warmup_model()
    
    print("\n🎉 Setup complete! Try these commands:")
    print("   python cli.py status")
    if ollama_running and model_available:
        print("   python cli.py ask 'Hello!'  # Should be fast now!")
    print("   python cli.py warmup        # Manually warm up model")
    print("   python cli.py chat")
    print("   python example.py")


if __name__ == "__main__":
    main()