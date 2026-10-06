import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import sms

print("Testing Gmail SMTP connection and live email delivery...")
TO = "polakash918@gmail.com"  # send to self as a real test
success, message = sms.send_gmail_otp(TO, "847291")

print(f"Success : {success}")
print(f"Message : {message}")
