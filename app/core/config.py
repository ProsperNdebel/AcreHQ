from typing import List, Union
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, field_validator
from dotenv import load_dotenv
load_dotenv()


class Settings(BaseSettings):
    # Project info
    PROJECT_NAME: str = "Zimbabwe Farmers Marketplace"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True
    PORT: int = 8000
    
    # CORS
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",
        "http://localhost:19006",  # Expo default
        "exp://localhost:19000",
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-make-it-long-and-random"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/zimbabwe_farmers_db"
    
    # Cloudinary (Image storage)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Africa's Talking (SMS)
    AFRICASTALKING_USERNAME: str = ""
    AFRICASTALKING_API_KEY: str = ""
    AFRICASTALKING_SENDER_ID: str = ""
    AFRICA_IS_TALKING_PROD_API_KEY: str = ""
    
    
    # Paynow (Payment gateway)
    PAYNOW_INTEGRATION_ID: str = ""
    PAYNOW_INTEGRATION_KEY: str = ""
    PAYNOW_RETURN_URL: str = ""
    PAYNOW_RESULT_URL: str = ""
    
    # Platform settings
    PLATFORM_COMMISSION_RATE: float = 0.05  # 15%
    MINIMUM_ORDER_AMOUNT: float = 5.0
    DELIVERY_FEE: float = 2.0
    
    # Google Maps
    GOOGLE_MAPS_API_KEY: str = ""


    # Add these fields to Settings class:
    PAYNOW_INTEGRATION_ID: str = "12345"
    PAYNOW_INTEGRATION_KEY: str = "mock-key-test"
    PAYNOW_RESULT_URL: str = "http://localhost:8000/api/v1/payments/webhook"
    PAYNOW_RETURN_URL: str = "myapp://payment-return"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()