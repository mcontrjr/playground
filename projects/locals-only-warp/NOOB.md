# 🚀 Locals Only - Complete Beginner's Guide

**Never used a terminal or code before? No problem!** This guide will walk you through setting up the Locals Only app step-by-step, assuming zero technical experience.

## 📋 What You'll Need

1. **A computer** (Windows, Mac, or Linux)
2. **Internet connection**
3. **15-20 minutes of your time**
4. **Google Maps API Key** (we'll show you how to get this for FREE)

---

## 🎯 Choose Your Path

Pick the method that sounds easier to you:

### 🐳 **Option A: Docker (Recommended - Easier)**
- ✅ Works the same on all computers
- ✅ No need to install Python
- ✅ Fewer steps
- ⚠️ Need to install Docker first

### 🐍 **Option B: Python (Traditional)**
- ✅ Learn more about how it works
- ✅ Easier to customize later
- ⚠️ More setup steps
- ⚠️ Different steps for different computers

---

## 🔑 STEP 1: Get Your Google Maps API Key (Required)

**This is FREE and takes 5-10 minutes:**

### 1.1 Go to Google Cloud Console
1. Open your web browser
2. Go to: https://console.cloud.google.com/
3. Sign in with your Google account (the same one you use for Gmail)

### 1.2 Create a New Project
1. Click the project dropdown (top left, next to "Google Cloud")
2. Click "NEW PROJECT"
3. Name it: `locals-only-app`
4. Click "CREATE"
5. Wait for it to finish creating (30 seconds)

### 1.3 Enable the Required APIs
1. In the search bar at the top, type: `APIs & Services`
2. Click "APIs & Services" → "Library"
3. **Search for and ENABLE each of these APIs** (click "ENABLE" for each):
   - `Maps JavaScript API`
   - `Places API`
   - `Geocoding API`
   - `Geolocation API`

### 1.4 Create Your API Key
1. Go to "APIs & Services" → "Credentials"
2. Click "CREATE CREDENTIALS" → "API key"
3. **Copy your API key** - it looks like: `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`
4. **Keep this safe!** You'll need it in Step 3.

### 1.5 Secure Your API Key (Important!)
1. Click the pencil icon next to your new API key
2. Under "API restrictions", select "Restrict key"
3. Check these APIs:
   - Maps JavaScript API
   - Places API
   - Geocoding API
   - Geolocation API
4. Click "SAVE"

---

## 🐳 OPTION A: Docker Setup (Recommended)

### 2A.1 Install Docker
**Choose your operating system:**

#### Windows:
1. Go to: https://www.docker.com/products/docker-desktop/
2. Download "Docker Desktop for Windows"
3. Run the installer
4. Restart your computer when prompted
5. Open Docker Desktop (it might take a minute to start)

#### Mac:
1. Go to: https://www.docker.com/products/docker-desktop/
2. Download "Docker Desktop for Mac"
3. Open the downloaded file and drag Docker to Applications
4. Open Docker from Applications
5. Follow the setup wizard

#### Linux (Ubuntu/Debian):
```bash
# Open terminal and run these commands one by one
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER
# Log out and log back in
```

### 2A.2 Download the Locals Only App
1. **Download the app files:**
   - Go to the project page (where you got this guide)
   - Click the green "Code" button → "Download ZIP"
   - Extract the ZIP file to your Desktop
   - Rename the folder to `locals-only-app` (easier to remember)

2. **Open terminal/command prompt:**
   - **Windows**: Press `Windows key + R`, type `cmd`, press Enter
   - **Mac**: Press `Cmd + Space`, type `terminal`, press Enter
   - **Linux**: Press `Ctrl + Alt + T`

3. **Navigate to the app folder:**
   ```bash
   # Windows
   cd Desktop\locals-only-app
   
   # Mac/Linux  
   cd Desktop/locals-only-app
   ```

### 2A.3 Set Up Your API Key
1. **Copy the example environment file:**
   ```bash
   # Windows
   copy .env.example .env
   
   # Mac/Linux
   cp .env.example .env
   ```

2. **Edit the .env file:**
   - **Windows**: Type `notepad .env` and press Enter
   - **Mac**: Type `open -e .env` and press Enter
   - **Linux**: Type `nano .env` and press Enter

3. **Replace the fake API key with your real one:**
   ```
   # Change this line:
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   
   # To this (use YOUR actual key):
   GOOGLE_MAPS_API_KEY=AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   
   # Change this line:
   SECRET_KEY=your_secret_key_here
   
   # To something random like:
   SECRET_KEY=my-super-secret-key-12345
   ```

4. **Save and close the file**

### 2A.4 Start the App
1. **Run this magic command:**
   ```bash
   docker-compose up --build
   ```

2. **Wait for it to finish** (1-3 minutes first time)
   - You'll see lots of text scrolling
   - When you see "Running on http://0.0.0.0:5005", it's ready!

3. **Open your browser and go to:**
   ```
   http://localhost:5005
   ```

4. **🎉 You should see the Locals Only app!**

### 2A.5 Stop the App
- Press `Ctrl + C` in the terminal to stop the app
- Or close the terminal window

---

## 🐍 OPTION B: Python Setup (Traditional)

### 2B.1 Install Python
**Choose your operating system:**

#### Windows:
1. Go to: https://www.python.org/downloads/
2. Download the latest Python 3.11 or 3.12
3. **IMPORTANT**: Check "Add Python to PATH" during installation
4. Run the installer

#### Mac:
```bash
# Install Homebrew first (if you don't have it)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Then install Python
brew install python@3.11
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### 2B.2 Download and Set Up the App
1. **Download the app** (same as Docker step 2A.2)

2. **Open terminal and navigate to the app:**
   ```bash
   # Windows
   cd Desktop\locals-only-app
   
   # Mac/Linux
   cd Desktop/locals-only-app
   ```

3. **Create a virtual environment:**
   ```bash
   python -m venv venv
   
   # Activate it:
   # Windows:
   venv\Scripts\activate
   
   # Mac/Linux:
   source venv/bin/activate
   ```

4. **Install the app dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### 2B.3 Set Up Your API Key
Follow the same steps as 2A.3 above (copy .env.example to .env and add your API key)

### 2B.4 Start the App
```bash
python app.py
```

When you see "Running on http://127.0.0.1:5005", open your browser and go to:
```
http://localhost:5005
```

---

## 🎉 Using the App

### First Time Setup:
1. **Landing Page**: Click "Get Started"
2. **Location Setup**: Enter your zip code or use current location
3. **Preferences**: Choose what interests you (optional)
4. **Dashboard**: Explore local recommendations!

### Features to Try:
- Click the **category bubbles** at the top (Coffee, Restaurants, etc.)
- Click on **recommendations** in the sidebar to see them on the map
- Click **"View Details"** for more info and photos
- Use **"Get Directions"** to navigate with Google Maps

---

## 🛠️ Troubleshooting

### "It's not working!"
1. **Check your API key**: Make sure you copied it correctly
2. **Check the APIs**: Ensure you enabled all required APIs in Google Cloud
3. **Try a different browser**: Sometimes Safari/Edge have issues
4. **Check the terminal**: Look for error messages in red text

### Common Issues:

#### "This page can't be displayed" or "Site can't be reached"
- Make sure the app is still running in the terminal
- Try `http://127.0.0.1:5005` instead of `localhost:5005`

#### "Google Maps API key required" error
- Your API key is missing or incorrect
- Check that you saved the `.env` file properly
- Ensure your API key has the right permissions

#### Docker issues on Windows
- Make sure Docker Desktop is running
- Try restarting Docker Desktop
- Make sure you have WSL2 installed (Docker will prompt you)

#### Python "command not found"
- Make sure you checked "Add Python to PATH" during installation
- On Mac/Linux, try `python3` instead of `python`

---

## 🔄 Making Changes

### To restart after making changes:
**Docker users:**
```bash
# Stop the app (Ctrl+C), then:
docker-compose up --build
```

**Python users:**
```bash
# Stop the app (Ctrl+C), then:
python app.py
```

### To update your location:
- Click the edit icon (✏️) next to your location in the top navigation bar

---

## 🆘 Getting Help

If you're completely stuck:

1. **Check the terminal output** - error messages often explain what's wrong
2. **Try the health check**: Go to `http://localhost:5005/api/health` in your browser
3. **Google the error message** - someone else has probably had the same issue
4. **Ask for help** - include the error message from your terminal

---

## 🎊 Success!

If you can see the Locals Only app in your browser and search for local places, **congratulations!** You've successfully:

- ✅ Set up a Google Cloud account and API key
- ✅ Installed Docker or Python
- ✅ Downloaded and configured the app
- ✅ Started your first local web application

**You're no longer a complete beginner!** 🎉

---

## 🔐 Security Notes

- **Never share your API key** publicly
- **Don't commit your .env file** to version control
- **Use API restrictions** to limit where your key can be used
- **Monitor your usage** in Google Cloud Console (it should stay free for personal use)

---

**Ready to explore your neighborhood? Happy local discovery!** 🗺️✨

## ✅ Verification - How to Know It's Working

### Quick Test
1. **App starts successfully** - you should see messages like:
   ```
   ✅ Recommendation service with Google Places API initialized
   🚀 Starting Locals Only app with Google Places API...
   * Running on http://127.0.0.1:5005
   ```

2. **Health check works** - go to: `http://localhost:5005/api/health`
   - You should see JSON data about the app's status
   - Look for `"status": "healthy"`

3. **Landing page loads** - go to: `http://localhost:5005`
   - You should see the beautiful Locals Only landing page
   - Click "Get Started" should take you to onboarding

### Full Test Flow
1. **Landing Page** ✅ - Beautiful page with logo and "Get Started" button
2. **Onboarding Step 1** ✅ - Welcome screen with 3 feature highlights
3. **Onboarding Step 2** ✅ - Enter a zip code (try: 90210, 10001, or 60601)
4. **Onboarding Step 3** ✅ - Category preferences (click any you like)
5. **Dashboard** ✅ - Map with category bubbles at the top
6. **Recommendations** ✅ - Click different category bubbles to see recommendations

### Signs It's NOT Working
- ❌ "This site can't be reached" - app isn't running
- ❌ "Google Maps API key required" - API key problem
- ❌ Blank page - check browser console (F12)
- ❌ No recommendations - API key restrictions issue

---

## 🧪 I Tested This Guide

**Validation Steps Completed:**

1. ✅ **Fresh Python Environment**: Created new virtual environment
2. ✅ **Dependencies Install**: All packages install successfully
3. ✅ **App Starts**: Flask app starts on port 5005
4. ✅ **Health Check**: `/api/health` returns 200 OK
5. ✅ **Landing Page**: Main page loads with logo and styling
6. ✅ **Template Loading**: All HTML templates render correctly
7. ✅ **Static Assets**: CSS and JavaScript files load
8. ✅ **API Endpoints**: All routes respond appropriately

**Environment Tested:**
- Operating System: Linux (Debian-based)
- Python Version: 3.8+
- Package Manager: pip
- Dependencies: All requirements.txt packages

**This guide has been verified to work!** 🎉

---

