import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app
import os

def enviar_email(destinatario, assunto, mensagem, html=None):
    """
    Função para enviar emails
    
    Args:
        destinatario (str): Email do destinatário
        assunto (str): Assunto do email
        mensagem (str): Corpo do email em texto plano
        html (str, optional): Corpo do email em HTML
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    # Configurações de email
    email_host = os.environ.get('EMAIL_HOST', 'smtp.example.com')
    email_port = int(os.environ.get('EMAIL_PORT', 587))
    email_user = os.environ.get('EMAIL_USER', 'seu_email@example.com')
    email_password = os.environ.get('EMAIL_PASSWORD', 'sua_senha')
    email_from = os.environ.get('EMAIL_FROM', 'Doce Sonho <contato@docesonho.com.br>')
    
    # Preparar mensagem
    msg = MIMEMultipart('alternative')
    msg['Subject'] = assunto
    msg['From'] = email_from
    msg['To'] = destinatario
    
    # Adicionar partes da mensagem
    part1 = MIMEText(mensagem, 'plain')
    msg.attach(part1)
    
    if html:
        part2 = MIMEText(html, 'html')
        msg.attach(part2)
    
    try:
        # Conectar ao servidor SMTP
        server = smtplib.SMTP(email_host, email_port)
        server.ehlo()
        server.starttls()
        server.login(email_user, email_password)
        
        # Enviar email
        server.sendmail(email_from, destinatario, msg.as_string())
        server.quit()
        
        return True
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False