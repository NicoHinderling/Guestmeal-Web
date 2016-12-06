#!/usr/bin/python
import sendgrid
import os
from sendgrid.helpers.mail import Email, Mail, Content
# from dotenv import Dotenv

# env = Dotenv('./.env')
env = os.environ

class ClientMail:
    def __init__(self):
        self.key = env['SENDGRID_KEY']
        self.sg = sendgrid.SendGridAPIClient(apikey= self.key)

    def send_email(self, to_email, subject, content):
        from_email = Email('info@guestmeal.me')
        to_email = Email(to_email)
        content = Content('text/plain', content)
        email = Mail(from_email, subject, to_email, content)
        response = self.sg.client.mail.send.post(request_body=email.get())
        return response.status_code, response.body, response.headers

       response = self.sg.client.mail.send.post(request_body=data)

    def send_transaction_emails(self, buyer_email, seller_email, price):
        formatted_price = format(price, '.2f')

        to_buyer_subject = "Guestmeal.me: Guestmeal Successfully Purchased!"
        to_buyer_content = "Hello,\nWe're just emailing you to let you know that you've successfully \
            purchased a Guestmeal from us for the price of ${0}.\nIn order to get your meal, please reach \
            out to the seller at {1}. We suggest using Venmo or cash. Let us know if you have any \
            questions!\nBest,\nGuestmeal.me\n".format(formatted_price, seller_email)

        self.send_email(buyer_email, to_buyer_subject, to_buyer_content)

        to_seller_subject = "Guestmeal.me: Guestmeal Successfully Sold!"
        to_seller_content = "Hello,\nWe're just emailing you to let you know that you've successfully \
            sold a Guestmeal with us for the price of ${0}.\nIn order for the buyer to get their meal, \
            please expect them to reach out to you via email ({1}). Let us know if you have any questions! \
            \nBest,\nGuestmeal.me\n".format(formatted_price, buyer_email)

        print(to_seller_content)

        self.send_email(seller_email, to_seller_subject, to_seller_content)
