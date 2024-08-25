import smtplib
import imghdr
from email.message import EmailMessage
import glob
import os


with open("web_credentials.txt") as user_file:
    USERNAME = user_file.readline()
    PASSWORD = user_file.readline()


# clean the img folder when needed - after sending email -
def clean_img_folder():
    print("folder clean started")
    images = glob.glob("images/*.png")
    for i in images:
        os.remove(i)
    print("folder clean ended")


def send_mail(image_path):
    print("email send started")
    email_message = EmailMessage()
    email_message["Subject"] = "Something appeared"
    email_message.set_content("A new object just appeared on the frame,"
                              " check it out:")
    with open(image_path, "rb") as file:
        content = file.read()
    email_message.add_attachment(content, maintype="image",
                                 subtype=imghdr.what(None, content))

    gmail = smtplib.SMTP("smtp.gmail.com", 587)
    gmail.ehlo()
    gmail.starttls()
    gmail.login(USERNAME, PASSWORD)
    gmail.sendmail(USERNAME, USERNAME, email_message.as_string())
    print("email send ended")
    clean_img_folder()


if __name__ == "__main__":
    send_mail(image_path="images/fondo.jpg")
