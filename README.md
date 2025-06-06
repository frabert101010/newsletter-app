# Bay Area Tech & News Weekly Newsletter

This automated newsletter system fetches the top 5 news articles about the San Francisco Bay Area and technology, and sends them weekly to your email address.

## Features

- Automated weekly newsletter delivery
- Beautiful HTML email template with blue header and white background
- Top 5 relevant news articles about Bay Area and tech
- Scheduled delivery every Monday at 9:00 AM

## Setup Instructions

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with the following variables:
   ```
   NEWS_API_KEY=your_newsapi_key
   EMAIL_FROM=your_gmail_address
   EMAIL_PASSWORD=your_gmail_app_password
   ```

   Note: 
   - Get your News API key from [NewsAPI](https://newsapi.org/)
   - For Gmail, you'll need to use an App Password. To create one:
     1. Enable 2-Step Verification in your Google Account
     2. Go to Security → App Passwords
     3. Generate a new app password for "Mail"

3. Run the newsletter script:
   ```bash
   python newsletter.py
   ```

## How It Works

The script will:
1. Run continuously in the background
2. Fetch news articles every Monday at 9:00 AM
3. Generate a beautiful HTML newsletter
4. Send it to the specified email address

To stop the script, press Ctrl+C in the terminal.

## Customization

You can modify the following in the `newsletter.py` file:
- Newsletter schedule (currently set to Monday at 9:00 AM)
- Email template design
- News search criteria
- Email recipient address 