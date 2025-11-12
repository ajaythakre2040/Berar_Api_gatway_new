from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from datetime import datetime


def send_reset_password_email(to_email, reset_link, user_name=None):
    print(f"✉️ Preparing to send password reset email to {to_email}")
    
    subject = "Reset your Api Gatway account password"
    from_email = f"Api Gatway <{settings.DEFAULT_FROM_EMAIL}>"
    year = datetime.now().year
    timestamp = datetime.now().strftime("%d %b %Y, %I:%M %p")
    print(f"🕒 Current timestamp for email: {timestamp}{from_email}{year}")
    # Use user_name if available, otherwise just say "Hi"
    greeting = f"Hi {user_name}," if user_name else "Hi,"

    text_content = f"""
{greeting}

We received a request on {timestamp} to reset the password for your Api Gatway account.

Click the link below to reset it:
{reset_link}

If you didn’t request this, please ignore this email.

Thanks,
Api Gatway Support Team
"""

    html_content = f"""
<html>
  <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; margin:0; padding:0;">
    <table width="100%" cellpadding="0" cellspacing="0" style="max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
      <tr>
        <td style="background-color: #004080; padding: 20px; color: #ffffff; text-align: center; border-top-left-radius: 8px; border-top-right-radius: 8px;">
          <h2 style="margin: 0;">Api Gatway</h2>
        </td>
      </tr>
      <tr>
        <td style="padding: 30px; color: #333333;">
          <p style="font-size: 16px;">{greeting}</p>
          <p style="font-size: 15px;">
            We received a request on <strong>{timestamp}</strong> to reset the password for your Api Gatway account.
          </p>
          <p style="font-size: 15px;">Click the button below to reset your password:</p>
          <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background-color: #007bff; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block;">
              Reset Password
            </a>
          </div>
          <p style="font-size: 14px;">
            If you didn’t request this, you can safely ignore this email.
          </p>
          <p style="font-size: 14px;">
            Thanks,<br/>Api Gatway Support Team
          </p>
        </td>
      </tr>
      <tr>
        <td style="background-color: #f0f0f0; padding: 20px; font-size: 12px; color: #666666; text-align: center; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
          &copy; {year} Api Gatway Pvt. Ltd.<br/>
          Contact: <a href="mailto:customercare@apigatway.com" style="color: #007bff; text-decoration: none;">customercare@apigatway.com</a>
        </td>
      </tr>
    </table>
  </body>
</html>
"""

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")
        result = msg.send()
        print(f"📤 Email successfully sent to {to_email} (result: {result})")
    except Exception as e:
        print(f"❌ Email send failed: {e}")
