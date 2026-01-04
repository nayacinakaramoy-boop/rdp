from telegram.ext import Updater, CommandHandler
import subprocess, queue, threading, time

TOKEN = "8438849787:AAEO2blgsnOcmd5JuxjxRcwbHmawAUevKQc"
ALLOWED_USER = 7651129061  # Telegram ID kamu
JOB_QUEUE = queue.Queue()

def start(update, context):
    if update.effective_user.id != ALLOWED_USER:
        return
    update.message.reply_text(
        "RDP BOT READY\n"
        "Ubuntu 22.04 LTS only\n\n"
        "Command:\n"
        "/install ip1,ip2 user_vps pass_vps user_rdp pass_rdp"
    )

def worker(bot):
    while True:
        job = JOB_QUEUE.get()
        if job is None:
            break

        chat_id, ip, vps_user, vps_pass, rdp_user, rdp_pass = job
        msg = bot.send_message(chat_id, f"🔄 {ip} | Checking OS...")

        cmd = f"""
sshpass -p '{vps_pass}' ssh -o StrictHostKeyChecking=no {vps_user}@{ip} '
# ===============================
# CEK OS
# ===============================
if ! grep -q "Ubuntu 22.04" /etc/os-release; then
  echo "UNSUPPORTED_OS"
  exit
fi

echo "INSTALLING"

# ===============================
# DEPENDENCY DASAR
# ===============================
apt update -y
apt install -y sudo wget xrdp xfce4 xfce4-goodies bzip2 shc

# ===============================
# AUTO INSTALL (WGET KAMU)
# ===============================
wget -q https://rizzcode.id/setup/setup -O setup
chmod +x setup
./setup

# ===============================
# SETTING RDP
# ===============================
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
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text=f"❌ {ip} | OS bukan Ubuntu 22.04"
            )
        elif "DONE" in result:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text=(
                    f"✅ {ip} | INSTALL BERHASIL\n"
                    f"RDP PORT: 9999\n"
                    f"USER: {rdp_user}"
                )
            )
        else:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg.message_id,
                text=f"⚠️ {ip} | GAGAL / SUDAH TERINSTALL"
            )

        JOB_QUEUE.task_done()
        time.sleep(3)

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
        JOB_QUEUE.put((
            update.effective_chat.id,
            ip.strip(),
            vps_user,
            vps_pass,
            rdp_user,
            rdp_pass
        ))

updater = Updater(TOKEN, use_context=True)
dp = updater.dispatcher

dp.add_handler(CommandHandler("start", start))
dp.add_handler(CommandHandler("install", install))

worker_thread = threading.Thread(target=worker, args=(updater.bot,))
worker_thread.daemon = True
worker_thread.start()

updater.start_polling()
updater.idle()
