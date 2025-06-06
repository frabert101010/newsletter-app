import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from newsletter import send_newsletter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///recipients.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model for recipients
class Recipient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    recipients = Recipient.query.all()
    return render_template('index.html', recipients=recipients)

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
    recipients = Recipient.query.all()
    if not recipients:
        flash('No recipients found!', 'error')
        return redirect(url_for('index'))
    
    try:
        for recipient in recipients:
            send_newsletter(recipient.email)
        flash('Newsletter sent successfully!', 'success')
    except Exception as e:
        flash(f'Error sending newsletter: {str(e)}', 'error')
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False) 