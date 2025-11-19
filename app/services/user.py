from typing import Optional, Dict, Any
import httpx    
from ..config.settings import settings


class UserService:
    
    def __init__(self):
        self.user_service_url = getattr(settings, 'USER_SERVICE_URL', "http://localhost:8000")
    
    async def verify_user_with_service(self, user_id: str) -> Optional[Dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            url = f"{self.user_service_url}/api/v1/users/{user_id}"
            print("Verifying user with URL:", url)
            try:
                response = await client.get(
                    url,
                    headers={"Authorization": f"Bearer {getattr(settings, 'SERVICE_TOKEN', 'internal-token')}"}
                )
                print(response.status_code, response.text)
                if response.status_code == 200:
                    return response.json()
                return None
            except httpx.RequestError:
                return None
    
    async def validate_user_exists(self, user_id: str) -> bool:
        user_data = await self.verify_user_with_service(user_id)
        return user_data is not None
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.verify_user_with_service(user_id)
    
    
    def verify_service_token(self, token: str) -> Optional[int]:
        from ..utils.security import verify_token
        try:
            payload = verify_token(token)
            if isinstance(payload, dict) and payload.get("type") == "service":
                return int(payload["sub"])
            return None
        except:
            return None
    
    def validate_credit_permissions(self, user_data: Dict[str, Any], credit_user_id: str) -> bool:
        if user_data.get("id") == credit_user_id:
            return True
        
        return user_data.get("role") == "admin"


user_service = UserService()