import os
import schedule
import time
from datetime import datetime, timedelta
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
    """Fetch top 5 news articles about America in Italian."""
    try:
        print("\n=== Fetching News Articles ===")
        print(f"Using News API Key: {os.getenv('NEWS_API_KEY')[:5]}...")  # Only show first 5 chars for security
        
        # Search for general American news in Italian with broader parameters
        query = '(USA OR "Stati Uniti" OR America)'
        print(f"Search Query: {query}")
        
        news = newsapi.get_everything(
            q=query,
            language='it',  # Get Italian news
            sort_by='relevancy',
            page_size=10,  # Increased to get more articles
            from_param=(datetime.now() - timedelta(days=15)).strftime('%Y-%m-%d')  # Last 15 days
        )
        
        print(f"News API Response Status: {news.get('status', 'No status')}")
        print(f"Total Results: {news.get('totalResults', 0)}")
        
        if news and 'articles' in news and news['articles']:
            articles = news['articles']
            print(f"Found {len(articles)} articles")
            for i, article in enumerate(articles, 1):
                print(f"\nArticle {i}:")
                print(f"Title: {article.get('title', 'No title')}")
                print(f"Description: {article.get('description', 'No description')[:100]}...")
                print(f"Source: {article.get('source', {}).get('name', 'Unknown')}")
                print(f"Published At: {article.get('publishedAt', 'Unknown')}")
            return articles[:5]  # Return top 5 most relevant articles
        else:
            print("No articles found in API response")
            print(f"Full API Response: {news}")
            return []
    except Exception as e:
        print(f"Error fetching news: {str(e)}")
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
            <h1>Notizie dagli Stati Uniti</h1>
        </div>
        <div class="content">
            <div class="date">Settimana del {{ current_date }}</div>
            <h2>Le Notizie Principali di Questa Settimana</h2>
            {% for article in articles %}
            <div class="article">
                <h2>{{ article.title }}</h2>
                <p>{{ article.description }}</p>
                <p><a href="{{ article.url }}" target="_blank">Leggi di più</a></p>
                <p class="original-link">Fonte: {{ article.source.name }}</p>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    
    template = Template(template)
    return template.render(articles=articles, current_date=datetime.now().strftime('%d %B %Y'))

def send_newsletter(recipient_email=None):
    """Send newsletter to specified email or default recipient."""
    try:
        articles = get_bay_area_news()
        if not articles:
            print("No articles found to send")
            return False
            
        html_content = generate_newsletter_html(articles)
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Notizie dagli Stati Uniti - {datetime.now().strftime('%d %B %Y')}"
        msg['From'] = os.getenv('EMAIL_USER')
        msg['To'] = recipient_email or "frabertolini91@gmail.com"
        
        # Attach HTML content
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect to SMTP server and send
        with smtplib.SMTP(os.getenv('EMAIL_SERVER'), int(os.getenv('EMAIL_PORT'))) as server:
            server.starttls()
            server.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))
            server.send_message(msg)
            
        print(f"Newsletter inviata con successo a {msg['To']} alle {datetime.now()}")
        return True
    except Exception as e:
        print(f"Errore nell'invio della newsletter: {e}")
        return False

def main():
    """Main function to schedule and run the newsletter every 30 seconds."""
    schedule.every(30).seconds.do(send_newsletter)
    print("Scheduler della newsletter avviato. Invio ogni 30 secondi. Premi Ctrl+C per uscire.")
    while True:
        schedule.run_pending()
        time.sleep(1)  # Check every second for pending tasks

if __name__ == "__main__":
    main() 