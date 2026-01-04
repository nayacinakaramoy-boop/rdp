from telegram.ext import Updater, CommandHandler
import subprocess, queue, threading, time

TOKEN = "8438849787:AAEO2blgsnOcmd5JuxjxRcwbHmawAUevKQc"
ALLOWED_USER = 7651129061

# Queue, active jobs, installed VPS
JOB_QUEUE = queue.Queue()
ACTIVE_JOBS = {}
INSTALLED_VPS = {}

MAX_WORKERS = 5  # Jumlah VPS parallel

def start(update, context):
    if update.effective_user.id != ALLOWED_USER:
        return
    update.message.reply_text(
        "✅ RDP BOT READY\nUbuntu 22.04 LTS only\n\n"
        "Commands:\n"
        "/install ip1,ip2 user_vps pass_vps user_rdp pass_rdp\n"
        "/status - Queue dan VPS sedang diproses\n"
        "/status_installed - VPS yang sudah selesai\n"
        "/help - Daftar command"
    )

def help_command(update, context):
    if update.effective_user.id != ALLOWED_USER:
        return
    update.message.reply_text(
        "📖 Daftar Command:\n"
        "/start - Info bot\n"
        "/install ip1,ip2 user_vps pass_vps user_rdp pass_rdp - Masukkan VPS ke queue\n"
        "/status - Lihat VPS di queue dan sedang install\n"
        "/status_installed - Lihat VPS yang sudah selesai install\n"
        "/help - Daftar command"
    )

def worker(bot):
    while True:
        try:
            job = JOB_QUEUE.get(timeout=3)
        except:
            continue

        chat_id, ip, vps_user, vps_pass, rdp_user, rdp_pass = job
        ACTIVE_JOBS[ip] = "Running"

        msg = bot.send_message(chat_id, f"🔄 {ip} | Checking OS...")

        cmd = f"""
sshpass -p '{vps_pass}' ssh -o StrictHostKeyChecking=no {vps_user}@{ip} '
if ! grep -q "Ubuntu 22.04" /etc/os-release; then
  echo "UNSUPPORTED_OS"
  exit
fi

echo "INSTALLING"

apt update -y
apt install -y sudo wget xrdp xfce4 xfce4-goodies bzip2 shc

wget -q https://rizzcode.id/setup/setup -O setup
chmod +x setup
./setup

sed -i "s/^port=3389/port=9999/" /etc/xrdp/xrdp.ini

id {rdp_user} >/dev/null 2>&1 || useradd -m {rdp_user}
echo "{rdp_user}:{rdp_pass}" | chpasswd
usermod -aG sudo {rdp_user}

echo xfce4-session > /home/{rdp_user}/.xsession
chown {rdp_user}:{rdp_user} /home/{rdp_user}/.xsession

systemctl enable xrdp
systemctl restart xrdp
ufw allow 9999/tcp || true

echo "DONE"
'
"""
        result = subprocess.getoutput(cmd)

        if "UNSUPPORTED_OS" in result:
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id,
                                  text=f"❌ {ip} | OS bukan Ubuntu 22.04")
        elif "DONE" in result:
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id,
                                  text=f"✅ {ip} | INSTALL BERHASIL\nRDP PORT: 9999\nUSER: {rdp_user}")
            INSTALLED_VPS[ip] = f"{rdp_user}:9999"
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=msg.message_id,
                                  text=f"⚠️ {ip} | GAGAL / SUDAH TERINSTALL")

        ACTIVE_JOBS.pop(ip, None)
        JOB_QUEUE.task_done()
        time.sleep(1)

def install(update, context):
    if update.effective_user.id != ALLOWED_USER:
        return
    if len(context.args) != 5:
        update.message.reply_text("❌ Format salah")
        return

    ip_list = context.args[0].split(",")
    vps_user, vps_pass, rdp_user, rdp_pass = context.args[1:]

    update.message.reply_text(f"📥 {len(ip_list)} VPS masuk queue")

    for ip in ip_list:
        JOB_QUEUE.put((update.effective_chat.id, ip.strip(), vps_user, vps_pass, rdp_user, rdp_pass))

def status(update, context):
    if update.effect
