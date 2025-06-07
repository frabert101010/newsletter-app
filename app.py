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
        subject = f"Notizie dagli Stati Uniti - {datetime.now().strftime('%d %B %Y')}"
        
        # Send to all recipients
        recipient_emails = [r.email for r in recipients]
        success = True
        for recipient in recipients:
            if not send_newsletter(recipient_email=recipient.email):
                success = False
                break
        
        if success:
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
        else:
            raise Exception("Failed to send newsletter to one or more recipients")
            
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
    
    print("\n=== Updating Schedule ===")
    print(f"Received form data:")
    print(f"- Frequency: {frequency}")
    print(f"- Day of week: {day_of_week}")
    print(f"- Day of month: {day_of_month}")
    print(f"- Time: {time}")
    
    try:
        schedule = Schedule.query.first()
        if not schedule:
            schedule = Schedule()
            db.session.add(schedule)
            print("Created new schedule")
        else:
            print(f"Found existing schedule:")
            print(f"- Current frequency: {schedule.frequency}")
            print(f"- Current active status: {schedule.active}")
        
        schedule.frequency = frequency
        schedule.day_of_week = int(day_of_week) if day_of_week else None
        schedule.day_of_month = int(day_of_month) if day_of_month else None
        schedule.time = time
        schedule.active = True
        
        db.session.commit()
        print("Schedule updated successfully:")
        print(f"- New frequency: {schedule.frequency}")
        print(f"- New active status: {schedule.active}")
        print("=== Schedule Update Completed ===\n")
        flash('Schedule updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"Error updating schedule: {str(e)}")
        print("=== Schedule Update Failed ===\n")
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
        print("\n=== Cron Job Started ===")
        print(f"Current time: {datetime.now()}")
        
        # Check if there's an active schedule
        schedule = Schedule.query.filter_by(active=True).first()
        if not schedule:
            print("No active schedule found in database")
            return "No active schedule found", 200

        print(f"Found active schedule:")
        print(f"- Frequency: {schedule.frequency}")
        print(f"- Time: {schedule.time}")
        print(f"- Active: {schedule.active}")
        print(f"- Day of week: {schedule.day_of_week}")
        print(f"- Day of month: {schedule.day_of_month}")

        # For minute frequency, send immediately
        if schedule.frequency == 'minute':
            print("Minute frequency detected - will send")
            send_now = True
        else:
            # For other frequencies, check if it's time to send
            current_time = datetime.now()
            scheduled_time = datetime.strptime(schedule.time, '%H:%M').time()
            current_time_only = current_time.time()
            
            # Check if current time matches scheduled time
            time_matches = (current_time_only.hour == scheduled_time.hour and 
                          current_time_only.minute == scheduled_time.minute)
            
            # Check day of week for weekly frequency
            if schedule.frequency == 'weekly' and schedule.day_of_week is not None:
                day_matches = current_time.weekday() == schedule.day_of_week
                send_now = time_matches and day_matches
            # Check day of month for monthly frequency
            elif schedule.frequency == 'monthly' and schedule.day_of_month is not None:
                day_matches = current_time.day == schedule.day_of_month
                send_now = time_matches and day_matches
            # For daily frequency, just check time
            else:
                send_now = time_matches

        if send_now:
            print("Time to send newsletter")
            # Get all active recipients
            recipients = Recipient.query.filter_by(active=True).all()
            print(f"Found {len(recipients)} active recipients")
            
            # Send to each recipient
            for recipient in recipients:
                print(f"Sending to recipient: {recipient.email}")
                if not send_newsletter(recipient_email=recipient.email):
                    raise Exception(f"Failed to send newsletter to {recipient.email}")
            
            print("=== Cron Job Completed Successfully ===")
            return "Newsletter sent successfully", 200
        else:
            print("Not time to send newsletter yet")
            return "Not time to send yet", 200
            
    except Exception as e:
        print(f"Error in cron job: {str(e)}")
        print("=== Cron Job Failed ===")
        return str(e), 500

@app.route('/cron/test')
def cron_test():
    """Test endpoint to verify cron job connectivity."""
    print("\n=== Cron Test Endpoint Called ===")
    print(f"Current time: {datetime.now()}")
    print("=== Cron Test Completed ===\n")
    return "Cron test successful", 200

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port) 