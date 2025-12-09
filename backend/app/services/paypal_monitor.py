"""
PayPal Integration Monitoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from app.utils.supabase_client import supabase
from app.middleware.metrics import paypal_api_calls, paypal_webhooks

logger = logging.getLogger(__name__)


class PayPalMonitor:
    """Monitor PayPal integration health"""
    
    def __init__(self):
        self.last_check = None
        self.is_running = False
    
    async def check_payment_health(self):
        """Check PayPal payment success rate"""
        try:
            # Get payments from last 24 hours
            cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            
            result = await asyncio.to_thread(
                lambda: supabase.table('payments')
                .select('status')
                .gte('created_at', cutoff)
                .execute()
            )
            
            if not result.data:
                return {'success_rate': None, 'total': 0}
            
            total = len(result.data)
            successful = sum(1 for p in result.data if p['status'] == 'completed')
            failed = total - successful
            success_rate = successful / total if total > 0 else 0
            
            # Update metrics
            paypal_api_calls.labels(operation='payment', status='success').inc(successful)
            paypal_api_calls.labels(operation='payment', status='failed').inc(failed)
            
            # Log warning if success rate is low
            if total > 0 and success_rate < 0.9:
                logger.warning(
                    f"PayPal payment success rate low: {success_rate:.1%} "
                    f"({successful}/{total} successful)"
                )
            
            return {
                'success_rate': success_rate,
                'total': total,
                'successful': successful,
                'failed': failed
            }
            
        except Exception as e:
            logger.error(f"Error checking PayPal payment health: {e}")
            return {'error': str(e)}
    
    async def check_webhook_health(self):
        """Check PayPal webhook delivery"""
        try:
            # Get webhooks from last hour
            cutoff = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            
            result = await asyncio.to_thread(
                lambda: supabase.table('webhook_events')
                .select('event_type, processed')
                .gte('created_at', cutoff)
                .execute()
            )
            
            if not result.data:
                return {'processing_rate': None, 'total': 0}
            
            total = len(result.data)
            processed = sum(1 for w in result.data if w['processed'])
            unprocessed = total - processed
            processing_rate = processed / total if total > 0 else 0
            
            # Update metrics
            for webhook in result.data:
                status = 'processed' if webhook['processed'] else 'pending'
                paypal_webhooks.labels(
                    event_type=webhook['event_type'],
                    processed=status
                ).inc()
            
            # Log warning if processing rate is low
            if total > 0 and processing_rate < 0.95:
                logger.warning(
                    f"PayPal webhook processing rate low: {processing_rate:.1%} "
                    f"({processed}/{total} processed, {unprocessed} pending)"
                )
            
            return {
                'processing_rate': processing_rate,
                'total': total,
                'processed': processed,
                'unprocessed': unprocessed
            }
            
        except Exception as e:
            logger.error(f"Error checking PayPal webhook health: {e}")
            return {'error': str(e)}
    
    async def check_subscription_health(self):
        """Check subscription creation and cancellation rates"""
        try:
            # Get subscriptions from last 7 days
            cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            result = await asyncio.to_thread(
                lambda: supabase.table('subscriptions')
                .select('status, subscription_tier, created_at, cancelled_at')
                .gte('created_at', cutoff)
                .execute()
            )
            
            if not result.data:
                return {'total': 0}
            
            total = len(result.data)
            active = sum(1 for s in result.data if s['status'] == 'active')
            cancelled = sum(1 for s in result.data if s.get('cancelled_at'))
            
            return {
                'total': total,
                'active': active,
                'cancelled': cancelled,
                'churn_rate': cancelled / total if total > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error checking subscription health: {e}")
            return {'error': str(e)}
    
    async def run_health_checks(self):
        """Run all health checks"""
        logger.info("Running PayPal health checks...")
        
        payment_health = await self.check_payment_health()
        webhook_health = await self.check_webhook_health()
        subscription_health = await self.check_subscription_health()
        
        self.last_check = datetime.utcnow()
        
        # Log summary
        logger.info(
            f"PayPal Health Check Complete:\n"
            f"  Payments: {payment_health}\n"
            f"  Webhooks: {webhook_health}\n"
            f"  Subscriptions: {subscription_health}"
        )
        
        return {
            'timestamp': self.last_check.isoformat(),
            'payments': payment_health,
            'webhooks': webhook_health,
            'subscriptions': subscription_health
        }
    
    async def start(self):
        """Start monitoring loop"""
        if self.is_running:
            logger.warning("PayPal monitor already running")
            return
        
        self.is_running = True
        logger.info("Starting PayPal monitor (checks every 10 minutes)")
        
        while self.is_running:
            try:
                await self.run_health_checks()
            except Exception as e:
                logger.error(f"PayPal monitor error: {e}")
            
            # Wait 10 minutes before next check
            await asyncio.sleep(600)
    
    def stop(self):
        """Stop monitoring loop"""
        self.is_running = False
        logger.info("Stopping PayPal monitor")


# Global instance
paypal_monitor = PayPalMonitor()