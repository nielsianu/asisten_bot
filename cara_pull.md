# 1. Tarik kode terbaru dari GitHub
git pull origin main

# 2. Update library (karena venv sudah aktif, langsung jalan)
#pip install -r requirements.txt

systemctl restart asisten_bot

# Cek status & log live-nya:
systemctl status asisten_bot
journalctl -u asisten_bot -f
