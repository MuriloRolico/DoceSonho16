import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
import os

def enviar_email(destinatario, assunto, mensagem, html=None):
    """
    Função para enviar emails com suporte completo a caracteres especiais
    
    Args:
        destinatario (str): Email do destinatário
        assunto (str): Assunto do email
        mensagem (str): Corpo do email em texto plano
        html (str, optional): Corpo do email em HTML
    
    Returns:
        bool: True se enviado com sucesso, False caso contrário
    """
    # Configurações de email
    email_host = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    email_port = int(os.environ.get('EMAIL_PORT', 587))
    email_user = os.environ.get('EMAIL_USER')
    email_password = os.environ.get('EMAIL_PASSWORD')
    email_from = os.environ.get('EMAIL_FROM', email_user)
    
    # Verificar se as credenciais essenciais estão definidas
    if not email_user or not email_password:
        print("Erro: EMAIL_USER e EMAIL_PASSWORD devem estar definidos nas variáveis de ambiente")
        return False
    
    try:
        # Preparar mensagem com encoding correto
        msg = MIMEMultipart('alternative')
        
        # Configurar headers com encoding UTF-8
        msg['Subject'] = Header(assunto, 'utf-8')
        msg['From'] = Header(email_from, 'utf-8')
        msg['To'] = Header(destinatario, 'utf-8')
        
        # Adicionar partes da mensagem com encoding UTF-8
        part1 = MIMEText(mensagem, 'plain', 'utf-8')
        msg.attach(part1)
        
        if html:
            part2 = MIMEText(html, 'html', 'utf-8')
            msg.attach(part2)
        
        # Conectar ao servidor SMTP
        with smtplib.SMTP(email_host, email_port) as server:
            server.ehlo()
            server.starttls()
            server.login(email_user, email_password)
            
            # Enviar email
            server.send_message(msg, from_addr=email_user, to_addrs=[destinatario])
        
        print(f"Email enviado com sucesso para {destinatario}")
        return True
        
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")
        return False