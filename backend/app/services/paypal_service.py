"""
PayPal API integration service.
Handles subscription creation, management, and webhook verification.
"""

from typing import Optional, Dict, Any, List
import requests
import base64
import hmac
import hashlib
import json
from datetime import datetime

from app.config import settings


class PayPalService:
    """Service for interacting with PayPal REST API v2"""
    
    def __init__(self):
        self.base_url = settings.PAYPAL_BASE_URL
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.secret = settings.PAYPAL_SECRET
        self.webhook_id = settings.PAYPAL_WEBHOOK_ID
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        
        # PayPal Plan IDs from config (supports both sandbox and production)
        self.PLAN_IDS = {
            'basic_monthly': settings.PAYPAL_PLAN_ID_BASIC,
            'pro_monthly': settings.PAYPAL_PLAN_ID_PRO,
        }
    
    def _get_access_token(self) -> str:
        """
        Get OAuth2 access token from PayPal.
        Caches token until expiration.
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        url = f"{self.base_url}/v1/oauth2/token"
        
        # Basic auth with client_id:secret
        auth = base64.b64encode(
            f"{self.client_id}:{self.secret}".encode()
        ).decode()
        
        headers = {
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {"grant_type": "client_credentials"}
        
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        
        result = response.json()
        self._access_token = result["access_token"]
        
        # Cache for 80% of expires_in time (safety margin)
        expires_in = result.get("expires_in", 3600)
        from datetime import timedelta
        self._token_expires_at = datetime.now() + timedelta(seconds=expires_in * 0.8)
        
        return self._access_token
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated request to PayPal API"""
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        )
        
        response.raise_for_status()
        
        # Some endpoints return 204 No Content
        if response.status_code == 204:
            return {"success": True}
        
        return response.json()
    
    def create_subscription(
        self,
        plan_id: str,
        return_url: str,
        cancel_url: str,
        user_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new PayPal subscription.
        
        Args:
            plan_id: PayPal plan ID (e.g., 'basic_monthly')
            return_url: URL to redirect after successful subscription
            cancel_url: URL to redirect if user cancels
            user_email: Optional subscriber email
        
        Returns:
            {
                "id": "I-SUBSCRIPTION-ID",
                "status": "APPROVAL_PENDING",
                "links": [
                    {"rel": "approve", "href": "https://paypal.com/..."}
                ]
            }
        """
        # Get actual PayPal plan ID
        paypal_plan_id = self.PLAN_IDS.get(plan_id)
        if not paypal_plan_id:
            raise ValueError(f"Unknown plan_id: {plan_id}")
        
        print(f"🔍 Creating subscription with plan: {plan_id} -> {paypal_plan_id}")
        print(f"📍 PayPal Base URL: {self.base_url}")
        
        data = {
            "plan_id": paypal_plan_id,
            "application_context": {
                "brand_name": "TailorJob",
                "locale": "en-US",
                "shipping_preference": "NO_SHIPPING",
                "user_action": "SUBSCRIBE_NOW",
                "return_url": return_url,
                "cancel_url": cancel_url
            }
        }
        
        # Add subscriber info if provided
        if user_email:
            data["subscriber"] = {
                "email_address": user_email
            }
        
        print(f"📤 Request data: {json.dumps(data, indent=2)}")
        
        try:
            result = self._make_request("POST", "/v1/billing/subscriptions", data=data)
            print(f"✅ PayPal response: {json.dumps(result, indent=2)}")
            return result
        except requests.exceptions.HTTPError as e:
            print(f"❌ PayPal error response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            raise
    
    def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details.
        
        Returns:
            {
                "id": "I-SUBSCRIPTION-ID",
                "plan_id": "P-PLAN-ID",
                "status": "ACTIVE",
                "billing_info": {...},
                "subscriber": {...}
            }
        """
        return self._make_request("GET", f"/v1/billing/subscriptions/{subscription_id}")
    
    def cancel_subscription(self, subscription_id: str, reason: str = "User requested cancellation") -> Dict[str, Any]:
        """
        Cancel a subscription.
        Subscription remains active until end of billing period.
        
        Args:
            subscription_id: PayPal subscription ID
            reason: Cancellation reason for analytics
        """
        data = {
            "reason": reason
        }
        
        return self._make_request(
            "POST",
            f"/v1/billing/subscriptions/{subscription_id}/cancel",
            data=data
        )
    
    def suspend_subscription(self, subscription_id: str, reason: str) -> Dict[str, Any]:
        """
        Suspend a subscription (payment failed, etc).
        Can be reactivated later.
        """
        data = {
            "reason": reason
        }
        
        return self._make_request(
            "POST",
            f"/v1/billing/subscriptions/{subscription_id}/suspend",
            data=data
        )
    
    def activate_subscription(self, subscription_id: str, reason: str) -> Dict[str, Any]:
        """
        Reactivate a suspended subscription.
        """
        data = {
            "reason": reason
        }
        
        return self._make_request(
            "POST",
            f"/v1/billing/subscriptions/{subscription_id}/activate",
            data=data
        )
    
    def get_transactions(
        self,
        subscription_id: str,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """
        Get subscription transactions (payments).
        
        Args:
            subscription_id: PayPal subscription ID
            start_time: ISO 8601 timestamp (e.g., '2025-01-01T00:00:00Z')
            end_time: ISO 8601 timestamp
        
        Returns:
            List of transaction objects
        """
        params = {
            "start_time": start_time,
            "end_time": end_time
        }
        
        response = self._make_request(
            "GET",
            f"/v1/billing/subscriptions/{subscription_id}/transactions",
            params=params
        )
        
        return response.get("transactions", [])
    
    def verify_webhook_signature(
        self,
        transmission_id: str,
        transmission_time: str,
        cert_url: str,
        auth_algo: str,
        transmission_sig: str,
        webhook_event: Dict[str, Any]
    ) -> bool:
        """
        Verify PayPal webhook signature.
        
        Args:
            transmission_id: From PayPal-Transmission-Id header
            transmission_time: From PayPal-Transmission-Time header
            cert_url: From PayPal-Cert-Url header
            auth_algo: From PayPal-Auth-Algo header
            transmission_sig: From PayPal-Transmission-Sig header
            webhook_event: Full webhook body as dict
        
        Returns:
            True if signature is valid
        """
        data = {
            "transmission_id": transmission_id,
            "transmission_time": transmission_time,
            "cert_url": cert_url,
            "auth_algo": auth_algo,
            "transmission_sig": transmission_sig,
            "webhook_id": self.webhook_id,
            "webhook_event": webhook_event
        }
        
        try:
            response = self._make_request(
                "POST",
                "/v1/notifications/verify-webhook-signature",
                data=data
            )
            
            return response.get("verification_status") == "SUCCESS"
        except Exception as e:
            print(f"Webhook verification failed: {e}")
            return False
    
    def get_plan_details(self, plan_id: str) -> Dict[str, Any]:
        """Get details of a billing plan"""
        return self._make_request("GET", f"/v1/billing/plans/{plan_id}")


# Singleton instance
paypal_service = PayPalService()