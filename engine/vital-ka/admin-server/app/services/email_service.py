# ──────────────────────────────────────────────
# Service Email (SMTP + Templates Jinja2)
# ──────────────────────────────────────────────
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from app.core.config import settings
from app.models import Doctor, User


class EmailService:
    def __init__(self):
        self.enabled = all([
            settings.smtp_host,
            settings.smtp_user,
            settings.smtp_password,
        ])
        
        # Templates
        template_dir = Path(__file__).parent.parent / "templates" / "email"
        template_dir.mkdir(parents=True, exist_ok=True)
        
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        
        # Créer templates par défaut s'ils n'existent pas
        self._create_default_templates(template_dir)

    def _create_default_templates(self, template_dir: Path):
        """Créer templates email par défaut"""
        templates = {
            "doctor_registration.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #1a73e8; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background: #1a73e8; color: white; text-decoration: none; border-radius: 4px; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Vital KA</h1>
        </div>
        <div class="content">
            <h2>Bienvenue Dr {{ doctor.first_name }} {{ doctor.last_name }}</h2>
            <p>Merci pour votre inscription sur Vital KA. Votre demande est en cours de vérification.</p>
            <p><strong>Numéro de licence :</strong> {{ doctor.license_number }}</p>
            <p><strong>Spécialité :</strong> {{ doctor.specialty or 'Non spécifiée' }}</p>
            <p>Vous recevrez un email dès que votre compte sera validé par notre équipe.</p>
            <p>Cordialement,<br>L'équipe Vital KA</p>
        </div>
        <div class="footer">
            <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
        </div>
    </div>
</body>
</html>
""",
            "doctor_validated.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #34a853; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background: #34a853; color: white; text-decoration: none; border-radius: 4px; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ Compte Validé</h1>
        </div>
        <div class="content">
            <h2>Félicitations Dr {{ doctor.first_name }} {{ doctor.last_name }} !</h2>
            <p>Votre compte Vital KA a été <strong>validé</strong>. Vous pouvez maintenant accéder à toutes les fonctionnalités.</p>
            <p><a href="{{ frontend_url }}/login" class="button">Se connecter à Vital KA</a></p>
            <p>Cordialement,<br>L'équipe Vital KA</p>
        </div>
        <div class="footer">
            <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
        </div>
    </div>
</body>
</html>
""",
            "doctor_rejected.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #ea4335; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>❌ Inscription Non Validée</h1>
        </div>
        <div class="content">
            <h2>Bonjour Dr {{ doctor.first_name }} {{ doctor.last_name }}</h2>
            <p>Après examen, nous ne pouvons pas valider votre inscription pour le moment.</p>
            <p><strong>Motif :</strong> {{ reason }}</p>
            <p>Vous pouvez corriger les éléments mentionnés et soumettre une nouvelle demande.</p>
            <p>Cordialement,<br>L'équipe Vital KA</p>
        </div>
        <div class="footer">
            <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
        </div>
    </div>
</body>
</html>
""",
            "password_reset.html": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #1a73e8; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background: #1a73e8; color: white; text-decoration: none; border-radius: 4px; }
        .footer { padding: 20px; text-align: center; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Réinitialisation Mot de Passe</h1>
        </div>
        <div class="content">
            <h2>Bonjour {{ user.first_name }}</h2>
            <p>Vous avez demandé la réinitialisation de votre mot de passe Vital KA Admin.</p>
            <p><a href="{{ reset_url }}" class="button">Réinitialiser mon mot de passe</a></p>
            <p>Ce lien expire dans 1 heure. Si vous n'avez pas fait cette demande, ignorez cet email.</p>
            <p>Cordialement,<br>L'équipe Vital KA</p>
        </div>
        <div class="footer">
            <p>Cet email a été envoyé automatiquement, merci de ne pas y répondre.</p>
        </div>
    </div>
</body>
</html>
""",
        }
        
        for name, content in templates.items():
            path = template_dir / name
            if not path.exists():
                path.write_text(content, encoding="utf-8")

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Envoyer email via SMTP"""
        if not self.enabled:
            print(f"[EMAIL DISABLED] To: {to_email}, Subject: {subject}")
            return False

        try:
            message = MIMEMultipart("alternative")
            message["From"] = settings.smtp_from
            message["To"] = to_email
            message["Subject"] = subject

            if text_content:
                message.attach(MIMEText(text_content, "plain", "utf-8"))
            message.attach(MIMEText(html_content, "html", "utf-8"))

            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_user,
                password=settings.smtp_password,
                use_tls=settings.smtp_use_tls,
            )
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False

    async def send_doctor_registration_confirmation(self, doctor: Doctor) -> bool:
        """Email confirmation inscription médecin"""
        template = self.jinja_env.get_template("doctor_registration.html")
        html = template.render(doctor=doctor, frontend_url=settings.frontend_url)
        return await self._send_email(
            doctor.email,
            "Bienvenue sur Vital KA - Inscription reçue",
            html,
        )

    async def send_doctor_validated(self, doctor: Doctor) -> bool:
        """Email validation médecin"""
        template = self.jinja_env.get_template("doctor_validated.html")
        html = template.render(doctor=doctor, frontend_url=settings.frontend_url)
        return await self._send_email(
            doctor.email,
            "✅ Votre compte Vital KA a été validé",
            html,
        )

    async def send_doctor_rejected(self, doctor: Doctor, reason: str) -> bool:
        """Email rejet médecin"""
        template = self.jinja_env.get_template("doctor_rejected.html")
        html = template.render(doctor=doctor, reason=reason, frontend_url=settings.frontend_url)
        return await self._send_email(
            doctor.email,
            "❌ Votre inscription Vital KA",
            html,
        )

    async def send_password_reset(self, user: User) -> bool:
        """Email reset password admin"""
        # TODO: Générer token reset
        reset_url = f"{settings.frontend_url}/reset-password?token=TODO"
        template = self.jinja_env.get_template("password_reset.html")
        html = template.render(user=user, reset_url=reset_url, frontend_url=settings.frontend_url)
        return await self._send_email(
            user.email,
            "🔐 Réinitialisation mot de passe Vital KA Admin",
            html,
        )

    async def send_doctor_password_reset(self, doctor: Doctor) -> bool:
        """Email reset password médecin"""
        reset_url = f"{settings.frontend_url}/doctor/reset-password?token=TODO"
        template = self.jinja_env.get_template("password_reset.html")
        html = template.render(user=doctor, reset_url=reset_url, frontend_url=settings.frontend_url)
        return await self._send_email(
            doctor.email,
            "🔐 Réinitialisation mot de passe Vital KA",
            html,
        )

    async def send_version_notification(
        self,
        emails: list[str],
        version_name: str,
        channel: str,
        download_url: str,
    ) -> bool:
        """Notification nouvelle version (pour testeurs beta)"""
        subject = f"📱 Nouvelle version Vital KA {version_name} ({channel})"
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Nouvelle version disponible</h2>
            <p>Version: <strong>{version_name}</strong></p>
            <p>Canal: <strong>{channel}</strong></p>
            <p><a href="{download_url}" style="background: #1a73e8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">Télécharger APK</a></p>
        </body>
        </html>
        """
        results = []
        for email in emails:
            results.append(await self._send_email(email, subject, html))
        return all(results)


email_service = EmailService()