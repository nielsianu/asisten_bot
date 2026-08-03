# 1. Tarik kode terbaru dari GitHub
git pull origin main

# 2. Update library (karena venv sudah aktif, langsung jalan)
pip install -r requirements.txt

# 3. Restart bot
sudo systemctl restart asisten_bot   # (atau sesuaikan dengan pm2/screen)
