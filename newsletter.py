import os
import schedule
import time
from datetime import datetime
from newsapi import NewsApiClient
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from jinja2 import Template
from dotenv import load_dotenv
from googletrans import Translator

# Load environment variables
load_dotenv()
print(f"Loaded NEWS_API_KEY: {os.getenv('NEWS_API_KEY')}")

# Initialize News API client
newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))

# Initialize translator
translator = Translator()

def translate_text(text):
    """Translate text from English to Italian."""
    try:
        translation = translator.translate(text, src='en', dest='it')
        return translation.text
    except Exception as e:
        print(f"Errore nella traduzione: {e}")
        return text

def get_bay_area_news():
    """Fetch top 5 news articles about Bay Area and tech in English and translate to Italian."""
    try:
        # Search for Bay Area and tech news in English
        news = newsapi.get_everything(
            q='(San Francisco OR "Bay Area") AND (tech OR technology)',
            language='en',  # Get English news
            sort_by='relevancy',
            page_size=5
        )
        
        if news and 'articles' in news:
            articles = news['articles']
            # Translate titles and descriptions
            for article in articles:
                article['title'] = translate_text(article['title'])
                article['description'] = translate_text(article['description'])
            return articles
        else:
            print("Nessun articolo trovato nella risposta API")
            return []
    except Exception as e:
        print(f"Errore nel recupero delle notizie: {e}")
        return []

def generate_newsletter_html(articles):
    """Generate HTML newsletter with the specified design in Italian."""
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                background-color: white;
            }
            .header {
                background-color: #1a73e8;
                color: white;
                padding: 20px;
                text-align: center;
            }
            .content {
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            .article {
                margin-bottom: 20px;
                padding: 15px;
                border-bottom: 1px solid #eee;
            }
            .article h2 {
                color: #1a73e8;
                margin-top: 0;
            }
            .article p {
                color: #333;
                line-height: 1.6;
            }
            .article a {
                color: #1a73e8;
                text-decoration: none;
            }
            .article a:hover {
                text-decoration: underline;
            }
            .date {
                color: #666;
                font-size: 0.9em;
                margin-bottom: 20px;
            }
            .original-link {
                font-size: 0.8em;
                color: #666;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Notizie Tech & Bay Area Settimanali</h1>
        </div>
        <div class="content">
            <div class="date">Settimana del {{ current_date }}</div>
            <h2>Le Notizie Principali di Questa Settimana</h2>
            {% for article in articles %}
            <div class="article">
                <h2>{{ article.title }}</h2>
                <p>{{ article.description }}</p>
                <p><a href="{{ article.url }}" target="_blank">Leggi di più</a></p>
                <p class="original-link">Articolo originale in inglese</p>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    
    template = Template(template)
    return template.render(articles=articles, current_date=datetime.now().strftime('%d %B %Y'))

def send_newsletter(html_content=None, recipient_email=None):
    """Send the newsletter via email."""
    try:
        # If no HTML content provided, generate it
        if html_content is None:
            # Get news articles
            articles = get_bay_area_news()
            if not articles:
                print("Nessun articolo trovato da inviare nella newsletter")
                return
            # Generate HTML content
            html_content = generate_newsletter_html(articles)
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Notizie Tech & Bay Area - {datetime.now().strftime('%d %B %Y')}"
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = recipient_email or "frabertolini91@gmail.com"
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Enable debug mode for SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(1)
        
        # Start TLS
        server.ehlo()
        server.starttls()
        server.ehlo()
        
        # Login with credentials
        email_user = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')
        
        if not email_user or not email_password:
            raise ValueError("Email credentials not found in environment variables")
            
        server.login(email_user, email_password)
        
        # Send email
        server.sendmail(email_user, msg['To'], msg.as_string())
        server.quit()
        
        print(f"Newsletter inviata con successo a {msg['To']} alle {datetime.now()}")
    except Exception as e:
        print(f"Errore nell'invio della newsletter: {e}")
        raise e

def main():
    """Main function to schedule and run the newsletter every 30 seconds."""
    schedule.every(30).seconds.do(send_newsletter)
    print("Scheduler della newsletter avviato. Invio ogni 30 secondi. Premi Ctrl+C per uscire.")
    while True:
        schedule.run_pending()
        time.sleep(1)  # Check every second for pending tasks

if __name__ == "__main__":
    main() 