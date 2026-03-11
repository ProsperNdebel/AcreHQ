import africastalking
from app.core.config import settings


class SMSService:
    def __init__(self):
        # Initialize Africa's Talking
        print(f'user name:{settings.AFRICASTALKING_USERNAME}\n api key:{settings.AFRICASTALKING_API_KEY}')
        africastalking.initialize(
            username=settings.AFRICASTALKING_USERNAME,
            api_key=settings.AFRICASTALKING_API_KEY
        )
        self.sms = africastalking.SMS
    
    async def send_otp(self, phone_number: str, otp_code: str) -> bool:
        """
        Send OTP code via SMS
        """
        try:
            # Ensure phone number starts with +
            if not phone_number.startswith('+'):
                phone_number = f'+{phone_number}'
            
            message = f"Your Zimbabwe Farmers Marketplace verification code is: {otp_code}. Valid for 10 minutes."
            
            response = self.sms.send(
                message=message,
                recipients=[phone_number],
                sender_id=settings.AFRICASTALKING_SENDER_ID
            )
            
            print(f"SMS sent to {phone_number}: {response} and the opt code is {otp_code}")
            return True
        except Exception as e:
            print(f"Error sending SMS: {str(e)}")
            return False
    
    async def send_notification(self, phone_number: str, message: str) -> bool:
        """
        Send general notification SMS
        """
        try:
            # Ensure phone number starts with +
            if not phone_number.startswith('+'):
                phone_number = f'+{phone_number}'
            
            response = self.sms.send(
                message=message,
                recipients=[phone_number],
                sender_id=settings.AFRICASTALKING_SENDER_ID
            )
            
            print(f"Notification sent to {phone_number}: {response}")
            return True
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return False
    
    # Update notification methods to check preferences:

    async def notify_order_placed(self, farmer_phone: str, crop_name: str, quantity: float, unit: str, farmer_prefs: dict = None) -> bool:
        """
        Notify farmer about new order
        """
        # Check if farmer wants new order notifications
        if farmer_prefs and not farmer_prefs.get('new_orders', True):
            return False
            
        message = f"New order! {quantity}{unit} of {crop_name}. Check your app to accept."
        return await self.send_notification(farmer_phone, message)

    async def notify_order_accepted(self, customer_phone: str, crop_name: str, customer_prefs: dict = None) -> bool:
        """
        Notify customer that order was accepted
        """
        # Check if customer wants order updates
        if customer_prefs and not customer_prefs.get('order_updates', True):
            return False
            
        message = f"Good news! Your order for {crop_name} has been accepted by the farmer."
        return await self.send_notification(customer_phone, message)

    async def notify_order_ready(self, customer_phone: str, crop_name: str, customer_prefs: dict = None) -> bool:
        """
        Notify customer that order is ready for pickup
        """
        # Check if customer wants order updates
        if customer_prefs and not customer_prefs.get('order_updates', True):
            return False
            
        message = f"Your order for {crop_name} is ready for pickup! Contact the farmer for details."
        return await self.send_notification(customer_phone, message)

    async def notify_order_completed(self, farmer_phone: str, customer_phone: str, crop_name: str, farmer_prefs: dict = None, customer_prefs: dict = None) -> bool:
        """
        Notify both parties that order is completed
        """
        farmer_msg = f"Order for {crop_name} marked as completed. Payment will be processed."
        customer_msg = f"Thank you for your purchase of {crop_name}! Enjoy your fresh produce."
        
        # Check farmer preferences
        if not farmer_prefs or farmer_prefs.get('payment_notifications', True):
            await self.send_notification(farmer_phone, farmer_msg)
        
        # Check customer preferences
        if not customer_prefs or customer_prefs.get('order_updates', True):
            await self.send_notification(customer_phone, customer_msg)
        
        return True

# Create singleton instance
sms_service = SMSService()