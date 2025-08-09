from app import app

if __name__ == '__main__':
    print("🚀 Starting Locals Only app...")
    print("🌐 Visit http://localhost:5005 to view the app")
    print("📱 The app is optimized for mobile devices")
    print("🔗 Other devices can access via http://[your-ip]:5005")
    app.run(debug=True, host='0.0.0.0', port=5005)
