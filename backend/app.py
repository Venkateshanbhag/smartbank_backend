import sqlite3
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.message import EmailMessage

# Initialize app and CORS
app = Flask(__name__)
CORS(app)

# Connect to database
conn = sqlite3.connect('bank.db', check_same_thread=False)
cursor = conn.cursor()

# Drop old table if exists (for development/testing only)
cursor.execute("DROP TABLE IF EXISTS accounts")

# Create new table with UNIQUE email constraint
cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unique_id TEXT NOT NULL UNIQUE,
        username TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        balance INTEGER NOT NULL
    )
''')
conn.commit()

# Email sending function
def send_email_notification(to_email, unique_id, username, balance):
    try:
        sender_email = 'baningsys22@gmail.com'
        app_password = 'zxjp ardm snoa sjmx'

        msg = EmailMessage()
        msg['Subject'] = 'Your Bank Account Unique ID'
        msg['From'] = sender_email
        msg['To'] = to_email

        msg.set_content(f'''Dear {username},

Your account has been created successfully.

Your Unique Login ID: {unique_id}
Initial Balance: ₹{balance}

🔐 Please keep this Unique ID secure. It acts as your login credential.

Thank you!
''')

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)

        print("Email sent successfully via Gmail.")
        return True

    except Exception as e:
        print(f"Gmail SMTP Exception: {e}")
        return False

# Route: Create Account
@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.json
    username = data['username']
    email = data['email']
    amount = int(data['amount'])

    unique_id = str(uuid.uuid4())[:8]

    try:
        cursor.execute("INSERT INTO accounts (unique_id, username, email, balance) VALUES (?, ?, ?, ?)", 
                      (unique_id, username, email, amount))
        conn.commit()

        email_sent = send_email_notification(email, unique_id, username, amount)

        return jsonify({
            "message": "Account created successfully! Check your email for the unique ID." if email_sent 
            else "Account created, but email failed to send.",
            "unique_id": unique_id  # For testing only
        })

    except sqlite3.IntegrityError as e:
        if 'email' in str(e).lower():
            return jsonify({"message": "This email is already associated with an account. Please delete the old account or use a different email."}), 400
        return jsonify({"message": f"Integrity error: {str(e)}"}), 400

    except sqlite3.Error as e:
        return jsonify({"message": f"Database error: {str(e)}"}), 400

# Route: Update Balance
@app.route('/update_balance', methods=['POST'])
def update_balance():
    data = request.json
    unique_id = data['unique_id']
    action = data['action']
    amount = int(data['amount'])

    cursor.execute("SELECT balance FROM accounts WHERE unique_id = ?", (unique_id,))
    account = cursor.fetchone()

    if not account:
        return jsonify({"message": "Account not found! Please check your unique ID."}), 404

    if action == "withdraw" and account[0] < amount:
        return jsonify({"message": "Insufficient balance!"}), 400

    new_balance = account[0] + amount if action == "deposit" else account[0] - amount
    cursor.execute("UPDATE accounts SET balance = ? WHERE unique_id = ?", (new_balance, unique_id))
    conn.commit()

    return jsonify({"message": f"{action.capitalize()} successful!", "balance": new_balance})

# Route: Delete Account
@app.route('/delete_account', methods=['POST'])
def delete_account():
    data = request.json
    unique_id = data['unique_id']

    cursor.execute("SELECT username FROM accounts WHERE unique_id = ?", (unique_id,))
    account = cursor.fetchone()

    if not account:
        return jsonify({"message": "Account not found! Please check your unique ID."}), 404

    cursor.execute("DELETE FROM accounts WHERE unique_id = ?", (unique_id,))
    conn.commit()

    return jsonify({"message": "Account deleted successfully!"})

# Route: Get Balance
@app.route('/get_balance', methods=['POST'])
def get_balance():
    data = request.json
    unique_id = data['unique_id']

    cursor.execute("SELECT balance FROM accounts WHERE unique_id = ?", (unique_id,))
    account = cursor.fetchone()

    if not account:
        return jsonify({"message": "Account not found! Please check your unique ID."}), 404

    return jsonify({"balance": account[0]})

# Run the app
if __name__ == '__main__':
     app.run(host='0.0.0.0', port=5000)
