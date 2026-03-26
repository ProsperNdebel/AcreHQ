import africastalking
from app.core.config import settings


class SMSService:
    def __init__(self):
        print(f'user name:{settings.AFRICASTALKING_USERNAME}\n api key:{settings.AFRICASTALKING_API_KEY}')
        africastalking.initialize(
            username=settings.AFRICASTALKING_USERNAME,
            api_key=settings.AFRICASTALKING_API_KEY
        )
        self.sms = africastalking.SMS

    def _build_sms_kwargs(self, message: str, recipients: list) -> dict:
        """Build SMS kwargs, only including sender_id if configured"""
        kwargs = {
            "message": message,
            "recipients": recipients,
        }
        if settings.AFRICASTALKING_SENDER_ID:
            kwargs["sender_id"] = settings.AFRICASTALKING_SENDER_ID
        return kwargs

    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        """Send OTP code via SMS"""
        try:
            if not phone_number.startswith('+'):
                phone_number = f'+{phone_number}'

            message = f"Your AcreHQ verification code is: {otp_code}. Valid for 10 minutes."
            kwargs = self._build_sms_kwargs(message, [phone_number])
            response = self.sms.send(**kwargs)

            print(f"SMS sent to {phone_number}: {response} and the otp code is {otp_code}")
            return True
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return False

    async def send_notification(self, phone_number: str, message: str) -> bool:
        """Send general notification SMS"""
        try:
            if not phone_number.startswith('+'):
                phone_number = f'+{phone_number}'

            kwargs = self._build_sms_kwargs(message, [phone_number])
            response = self.sms.send(**kwargs)

            print(f"Notification sent to {phone_number}: {response}")
            return True
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False

    async def notify_order_placed(self, farmer_phone: str, crop_name: str, quantity: float, unit: str, farmer_prefs: dict = None) -> bool:
        """Notify farmer about new order"""
        if farmer_prefs and not farmer_prefs.get('new_orders', True):
            return False

        message = f"New order! {quantity}{unit} of {crop_name}. Check your app to accept."
        return await self.send_notification(farmer_phone, message)

    async def notify_order_accepted(self, customer_phone: str, crop_name: str, customer_prefs: dict = None) -> bool:
        """Notify customer that order was accepted"""
        if customer_prefs and not customer_prefs.get('order_updates', True):
            return False

        message = f"Good news! Your order for {crop_name} has been accepted by the farmer."
        return await self.send_notification(customer_phone, message)

    async def notify_order_ready(self, customer_phone: str, crop_name: str, customer_prefs: dict = None) -> bool:
        """Notify customer that order is ready for pickup"""
        if customer_prefs and not customer_prefs.get('order_updates', True):
            return False

        message = f"Your order for {crop_name} is ready for pickup! Contact the farmer for details."
        return await self.send_notification(customer_phone, message)

    async def notify_order_completed(self, farmer_phone: str, customer_phone: str, crop_name: str, farmer_prefs: dict = None, customer_prefs: dict = None) -> bool:
        """Notify both parties that order is completed"""
        farmer_msg = f"Order for {crop_name} marked as completed. Payment will be processed."
        customer_msg = f"Thank you for your purchase of {crop_name}! Enjoy your fresh produce."

        if not farmer_prefs or farmer_prefs.get('payment_notifications', True):
            await self.send_notification(farmer_phone, farmer_msg)

        if not customer_prefs or customer_prefs.get('order_updates', True):
            await self.send_notification(customer_phone, customer_msg)

        return True


# Create singleton instance
sms_service = SMSService()