import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from newsletter import send_newsletter, get_bay_area_news, generate_newsletter_html
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///recipients.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database models
class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class NewsletterHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    recipients = db.Column(db.Text)  # Store as comma-separated list
    status = db.Column(db.String(20))  # 'success' or 'error'
    error_message = db.Column(db.Text, nullable=True)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    frequency = db.Column(db.String(20))  # 'daily', 'weekly', 'monthly'
    day_of_week = db.Column(db.Integer, nullable=True)  # 0-6 for weekly
    day_of_month = db.Column(db.Integer, nullable=True)  # 1-31 for monthly
    time = db.Column(db.String(5))  # HH:MM format
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    recipients = Recipient.query.all()
    history = NewsletterHistory.query.order_by(NewsletterHistory.sent_at.desc()).limit(10).all()
    schedule = Schedule.query.first()
    return render_template('index.html', recipients=recipients, history=history, schedule=schedule)

@app.route('/add_recipient', methods=['POST'])
def add_recipient():
    email = request.form.get('email')
    if email:
        try:
            recipient = Recipient(email=email)
            db.session.add(recipient)
            db.session.commit()
            flash('Recipient added successfully!', 'success')
        except:
            db.session.rollback()
            flash('Email already exists!', 'error')
    return redirect(url_for('index'))

@app.route('/delete_recipient/<int:id>')
def delete_recipient(id):
    recipient = Recipient.query.get_or_404(id)
    db.session.delete(recipient)
    db.session.commit()
    flash('Recipient deleted successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/send_newsletter')
def send_newsletter_route():
    recipients = Recipient.query.filter_by(active=True).all()
    if not recipients:
        flash('No active recipients found!', 'error')
        return redirect(url_for('index'))
    
    try:
        # Generate newsletter content
        articles = get_bay_area_news()
        if not articles:
            flash('No articles found to send!', 'error')
            return redirect(url_for('index'))
        
        html_content = generate_newsletter_html(articles)
        subject = f"Notizie Tech & Bay Area - {datetime.now().strftime('%d %B %Y')}"
        
        # Send to all recipients
        recipient_emails = [r.email for r in recipients]
        for recipient in recipients:
            send_newsletter(html_content=html_content, recipient_email=recipient.email)
        
        # Record in history
        history_entry = NewsletterHistory(
            subject=subject,
            content=html_content,
            recipients=','.join(recipient_emails),
            status='success'
        )
        db.session.add(history_entry)
        db.session.commit()
        
        flash('Newsletter sent successfully!', 'success')
    except Exception as e:
        # Record error in history
        history_entry = NewsletterHistory(
            subject=subject if 'subject' in locals() else 'Failed newsletter',
            content=html_content if 'html_content' in locals() else '',
            recipients=','.join(recipient_emails) if 'recipient_emails' in locals() else '',
            status='error',
            error_message=str(e)
        )
        db.session.add(history_entry)
        db.session.commit()
        
        flash(f'Error sending newsletter: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/update_schedule', methods=['POST'])
def update_schedule():
    frequency = request.form.get('frequency')
    day_of_week = request.form.get('day_of_week')
    day_of_month = request.form.get('day_of_month')
    time = request.form.get('time')
    
    print(f"Updating schedule with: frequency={frequency}, day_of_week={day_of_week}, day_of_month={day_of_month}, time={time}")
    
    try:
        schedule = Schedule.query.first()
        if not schedule:
            schedule = Schedule()
            db.session.add(schedule)
            print("Created new schedule")
        else:
            print(f"Found existing schedule: active={schedule.active}")
        
        schedule.frequency = frequency
        schedule.day_of_week = int(day_of_week) if day_of_week else None
        schedule.day_of_month = int(day_of_month) if day_of_month else None
        schedule.time = time
        schedule.active = True
        
        db.session.commit()
        print(f"Schedule updated successfully: active={schedule.active}")
        flash('Schedule updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error updating schedule: {str(e)}")
        flash(f'Error updating schedule: {str(e)}', 'error')
    
    return redirect(url_for('index'))

@app.route('/toggle_schedule')
def toggle_schedule():
    schedule = Schedule.query.first()
    if schedule:
        schedule.active = not schedule.active
        db.session.commit()
        status = 'activated' if schedule.active else 'deactivated'
        flash(f'Schedule {status}!', 'success')
    return redirect(url_for('index'))

@app.route('/view_newsletter/<int:id>')
def view_newsletter(id):
    newsletter = NewsletterHistory.query.get_or_404(id)
    return render_template('view_newsletter.html', newsletter=newsletter)

@app.route('/cron/send-newsletter')
def cron_send_newsletter():
    """Endpoint for Render's cron job to trigger newsletter sending."""
    try:
        print("Cron job triggered")
        # Check if there's an active schedule
        schedule = Schedule.query.filter_by(active=True).first()
        if not schedule:
            print("No active schedule found")
            return "No active schedule found", 200

        print(f"Found active schedule: frequency={schedule.frequency}, time={schedule.time}")
        # Check if it's time to send based on schedule
        now = datetime.now()
        should_send = False

        if schedule.frequency == 'minute':
            should_send = True
            print("Minute frequency - will send")
        elif schedule.frequency == 'daily':
            should_send = True
            print("Daily frequency - will send")
        elif schedule.frequency == 'weekly':
            if now.weekday() == schedule.day_of_week:
                should_send = True
                print(f"Weekly frequency - today is the right day (weekday={now.weekday()}, scheduled={schedule.day_of_week})")
            else:
                print(f"Weekly frequency - wrong day (weekday={now.weekday()}, scheduled={schedule.day_of_week})")
        elif schedule.frequency == 'monthly':
            if now.day == schedule.day_of_month:
                should_send = True
                print(f"Monthly frequency - today is the right day (day={now.day}, scheduled={schedule.day_of_month})")
            else:
                print(f"Monthly frequency - wrong day (day={now.day}, scheduled={schedule.day_of_month})")

        # Check if it's the right time
        if should_send:
            if schedule.frequency == 'minute':
                # For minute frequency, send immediately
                send_now = True
                print("Minute frequency - sending now")
            else:
                schedule_time = datetime.strptime(schedule.time, '%H:%M').time()
                send_now = now.time().hour == schedule_time.hour and now.time().minute == schedule_time.minute
                print(f"Checking time: current={now.time()}, scheduled={schedule_time}, send_now={send_now}")

            if send_now:
                print("Time to send newsletter")
                # Generate newsletter content
                articles = get_bay_area_news()
                if not articles:
                    print("No articles found to send")
                    return "No articles found to send", 200
                
                print(f"Found {len(articles)} articles")
                html_content = generate_newsletter_html(articles)
                subject = f"Notizie Tech & Bay Area - {now.strftime('%d %B %Y')}"
                
                # Get all active recipients
                recipients = Recipient.query.filter_by(active=True).all()
                if not recipients:
                    print("No active recipients found")
                    return "No active recipients found", 200
                
                print(f"Found {len(recipients)} active recipients")
                # Send to all recipients
                recipient_emails = [r.email for r in recipients]
                for recipient in recipients:
                    send_newsletter(html_content=html_content, recipient_email=recipient.email)
                
                # Record in history
                history_entry = NewsletterHistory(
                    subject=subject,
                    content=html_content,
                    recipients=','.join(recipient_emails),
                    status='success'
                )
                db.session.add(history_entry)
                db.session.commit()
                
                print("Newsletter sent successfully")
                return "Newsletter sent successfully", 200
            else:
                print("Not the scheduled time yet")
                return "Not the scheduled time yet", 200
        else:
            print("Not the scheduled day")
            return "Not the scheduled day", 200
            
    except Exception as e:
        print(f"Error in cron job: {str(e)}")
        # Record error in history
        history_entry = NewsletterHistory(
            subject="Failed automated newsletter",
            content="",
            recipients="",
            status='error',
            error_message=str(e)
        )
        db.session.add(history_entry)
        db.session.commit()
        
        return f"Error sending newsletter: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 