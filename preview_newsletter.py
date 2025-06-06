from jinja2 import Template

# Sample news articles for preview
sample_articles = [
    {
        'title': 'San Francisco Tech Companies Announce Major AI Breakthrough',
        'description': 'Leading tech companies in the Bay Area have unveiled a new artificial intelligence system that promises to revolutionize how we interact with technology.',
        'url': 'https://example.com/ai-news'
    },
    {
        'title': 'New Tech Hub Opens in Oakland',
        'description': 'A new technology innovation center has opened its doors in downtown Oakland, bringing hundreds of new jobs to the East Bay area.',
        'url': 'https://example.com/oakland-tech'
    },
    {
        'title': 'Silicon Valley Startup Raises $50M in Series B Funding',
        'description': 'A promising startup focused on sustainable technology has secured significant funding, marking a strong recovery in the Bay Area tech investment scene.',
        'url': 'https://example.com/startup-news'
    },
    {
        'title': 'San Francisco Hosts Annual Tech Conference',
        'description': 'Thousands of tech professionals gathered in San Francisco for the annual technology conference, featuring keynote speeches from industry leaders.',
        'url': 'https://example.com/tech-conference'
    },
    {
        'title': 'Bay Area Companies Lead in Green Technology',
        'description': 'Several Bay Area companies are making significant strides in developing sustainable and eco-friendly technology solutions.',
        'url': 'https://example.com/green-tech'
    }
]

def generate_newsletter_html(articles):
    """Generate HTML newsletter with the specified design."""
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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Bay Area Tech & News Weekly</h1>
        </div>
        <div class="content">
            <div class="date">Week of March 18, 2024</div>
            <h2>Top Stories This Week</h2>
            {% for article in articles %}
            <div class="article">
                <h2>{{ article.title }}</h2>
                <p>{{ article.description }}</p>
                <p><a href="{{ article.url }}" target="_blank">Read more</a></p>
            </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    
    template = Template(template)
    return template.render(articles=articles)

# Generate the newsletter
html_content = generate_newsletter_html(sample_articles)

# Save to a file
with open('newsletter_preview.html', 'w') as f:
    f.write(html_content)

print("Newsletter preview has been generated as 'newsletter_preview.html'") 