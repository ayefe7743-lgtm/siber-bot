import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Logging ayarları
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Durumlar
EMAIL, SUBJECT, DESCRIPTION = range(3)

# SMTP Bilgileri (Kendi Gmail ve Uygulama Şifrenizi buraya yazın)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "senin_mailin@gmail.com"
SENDER_PASSWORD = "gmail_uygulama_sifresi"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Süreci başlatır ve kullanıcıdan e-posta adresini ister."""
    await update.message.reply_text(
        "Siber güvenlik olay bildirim sistemine hoş geldiniz.\n\n"
        "Lütfen yetkililerin size geri dönebilmesi için kendi e-posta adresinizi girin:"
    )
    return EMAIL


async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Kullanıcının e-postasını kaydeder ve konu başlığını sorar."""
    context.user_data["reporter_email"] = update.message.text
    await update.message.reply_text(
        "Teşekkürler. Şimdi bildirim için kısa bir **konu başlığı** girin:"
    )
    return SUBJECT


async def get_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Konu başlığını kaydeder ve detaylı açıklamayı ister."""
    context.user_data["subject"] = update.message.text
    await update.message.reply_text(
        "Lütfen karşılaştığınız durumu veya ihbarı detaylı bir şekilde **açıklayın**:"
    )
    return DESCRIPTION


async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Açıklamayı alır, e-postayı gönderir ve süreci sonlandırır."""
    context.user_data["description"] = update.message.text

    reporter_email = context.user_data["reporter_email"]
    subject = context.user_data["subject"]
    description = context.user_data["description"]

    # E-posta Gönderim Mantığı
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = SENDER_EMAIL  # Raporun iletileceği yetkili adres
        msg["Subject"] = f"[RedTeam İhbar] {subject}"

        # Kritik Reply-To başlığı: Yetkili "Yanıtla" dediğinde doğrudan kullanıcının mailine gider
        msg["Add_Header"] = ("Reply-To", reporter_email)
        # Standart python kütüphanesi için header ekleme alternatifi:
        msg.add_header("Reply-To", reporter_email)

        body = (
            f"Yeni bir siber güvenlik olayı bildirildi.\n\n"
            f"Bildiren Kullanıcı E-posta: {reporter_email}\n"
            f"Konu: {subject}\n\n"
            f"Açıklama:\n{description}"
        )
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        await update.message.reply_text(
            "✅ İhbarınız başarıyla yetkili birime e-posta olarak iletildi. "
            "Gerekirse yetkililer sizinle belirttiğiniz e-posta üzerinden iletişime geçecektir."
        )
    except Exception as e:
        logger.error(f"E-posta gönderilemedi: {e}")
        await update.message.reply_text(
            "❌ E-posta gönderilirken teknik bir hata oluştu. Lütfen daha sonra tekrar deneyin."
        )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Süreci iptal eder."""
    await update.message.reply_text("İşlem iptal edildi.")
    return ConversationHandler.END


def main():
    # Botun Token Bilgisi
    TOKEN = "8838569129:AAHHnEk2da3blwPkWdLQqPbe0iV33kpA1G4"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            SUBJECT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_subject)
            ],
            DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Botu başlat
    print("Bot çalışıyor...")
    app.run_polling()


if __name__ == "__main__":
    main()
