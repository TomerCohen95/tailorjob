import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Check, Loader2, Crown, Zap } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { paymentsAPI, type Subscription, type UsageData } from '@/lib/api';

interface PricingTier {
  id: 'free' | 'basic' | 'pro';
  name: string;
  price: string;
  priceMonthly: number;
  description: string;
  features: string[];
  highlighted?: boolean;
  icon: typeof Zap;
}

const PRICING_TIERS: PricingTier[] = [
  {
    id: 'free',
    name: 'Free',
    price: '$0',
    priceMonthly: 0,
    description: 'Perfect for trying out TailorJob',
    icon: Zap,
    features: [
      '3 CV uploads',
      '5 job matches per month',
      'Basic matching algorithm',
      'Email support',
    ],
  },
  {
    id: 'basic',
    name: 'Basic',
    price: '$9.99',
    priceMonthly: 9.99,
    description: 'Great for active job seekers',
    icon: Check,
    highlighted: true,
    features: [
      '10 CV uploads',
      '50 job matches per month',
      '5 tailored CVs per month',
      'Advanced matching algorithm',
      'Priority email support',
      'Match score explanations',
    ],
  },
  {
    id: 'pro',
    name: 'Pro',
    price: '$19.99',
    priceMonthly: 19.99,
    description: 'For serious professionals',
    icon: Crown,
    features: [
      'Unlimited CV uploads',
      'Unlimited job matches',
      'Unlimited tailored CVs',
      'Premium matching algorithm',
      '24/7 priority support',
      'Detailed match analytics',
      'CV revision history',
      'Export to PDF',
    ],
  },
];

export default function Pricing() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState<string | null>(null);
  const [currentSubscription, setCurrentSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    loadSubscriptionData();
  }, []);

  const loadSubscriptionData = async () => {
    try {
      const [sub, usageData] = await Promise.all([
        paymentsAPI.getSubscription(),
        paymentsAPI.getUsage(),
      ]);
      setCurrentSubscription(sub);
      setUsage(usageData);
    } catch (error) {
      console.error('Failed to load subscription data:', error);
    } finally {
      setLoadingData(false);
    }
  };

  const handleSubscribe = async (tier: 'basic' | 'pro') => {
    setLoading(tier);
    try {
      const response = await paymentsAPI.createSubscription(tier);
      
      // Redirect to PayPal approval URL
      window.location.href = response.approval_url;
    } catch (error) {
      console.error('Failed to create subscription:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to create subscription',
        variant: 'destructive',
      });
      setLoading(null);
    }
  };

  const handleUpgrade = async (newTier: 'basic' | 'pro') => {
    setLoading(newTier);
    try {
      const response = await paymentsAPI.upgradeSubscription(newTier);
      
      // Redirect to PayPal approval URL
      window.location.href = response.approval_url;
    } catch (error) {
      console.error('Failed to upgrade subscription:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to upgrade subscription',
        variant: 'destructive',
      });
      setLoading(null);
    }
  };

  const handleCancelSubscription = async () => {
    if (!confirm('Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your billing period.')) {
      return;
    }

    setLoading('cancel');
    try {
      await paymentsAPI.cancelSubscription();
      toast({
        title: 'Subscription Cancelled',
        description: 'Your subscription has been cancelled. You will retain access until the end of your billing period.',
      });
      await loadSubscriptionData();
    } catch (error) {
      console.error('Failed to cancel subscription:', error);
      toast({
        title: 'Error',
        description: error instanceof Error ? error.message : 'Failed to cancel subscription',
        variant: 'destructive',
      });
    } finally {
      setLoading(null);
    }
  };

  const getCurrentTier = (): 'free' | 'basic' | 'pro' => {
    if (!currentSubscription || currentSubscription.status !== 'active') {
      return 'free';
    }
    return currentSubscription.tier;
  };

  const isCurrentTier = (tier: 'free' | 'basic' | 'pro') => {
    return getCurrentTier() === tier;
  };

  const canUpgradeTo = (tier: 'basic' | 'pro') => {
    const current = getCurrentTier();
    if (current === 'free') return true;
    if (current === 'basic' && tier === 'pro') return true;
    return false;
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/20">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold mb-4">Choose Your Plan</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Select the perfect plan for your job search journey. Upgrade or downgrade anytime.
          </p>
        </div>

        {/* Current Usage Stats */}
        <Card className="max-w-4xl mx-auto mb-12 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/20 dark:to-indigo-950/20 border-blue-200 dark:border-blue-800">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-blue-600" />
              Your Current Usage
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingData ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">CV Uploads</div>
                  <div className="h-8 bg-muted animate-pulse rounded w-24"></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Job Matches</div>
                  <div className="h-8 bg-muted animate-pulse rounded w-24"></div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Tailored CVs</div>
                  <div className="h-8 bg-muted animate-pulse rounded w-24"></div>
                </div>
              </div>
            ) : usage ? (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">CV Uploads</div>
                  <div className="text-2xl font-bold">
                    {usage.cv_uploads} / {usage.cv_limit === -1 ? '∞' : usage.cv_limit}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Job Matches</div>
                  <div className="text-2xl font-bold">
                    {usage.job_matches} / {usage.match_limit === -1 ? '∞' : usage.match_limit}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">Tailored CVs</div>
                  <div className="text-2xl font-bold">
                    {usage.tailored_cvs} / {usage.tailor_limit === -1 ? '∞' : usage.tailor_limit}
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center text-muted-foreground py-4">
                Unable to load usage data
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {PRICING_TIERS.map((tier) => {
            const Icon = tier.icon;
            const isCurrent = isCurrentTier(tier.id);
            const canUpgrade = tier.id !== 'free' && canUpgradeTo(tier.id);
            
            return (
              <Card 
                key={tier.id}
                className={`relative ${
                  tier.highlighted 
                    ? 'border-2 border-primary shadow-lg scale-105' 
                    : ''
                } ${isCurrent ? 'bg-muted/50' : ''}`}
              >
                {tier.highlighted && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-primary text-primary-foreground px-4 py-1">
                      Most Popular
                    </Badge>
                  </div>
                )}
                
                {isCurrent && (
                  <div className="absolute -top-4 right-4">
                    <Badge variant="secondary" className="px-4 py-1">
                      Current Plan
                    </Badge>
                  </div>
                )}

                <CardHeader>
                  <div className="flex items-center justify-between mb-2">
                    <CardTitle className="text-2xl flex items-center gap-2">
                      <Icon className="h-6 w-6" />
                      {tier.name}
                    </CardTitle>
                  </div>
                  <div className="mb-2">
                    <span className="text-4xl font-bold">{tier.price}</span>
                    {tier.priceMonthly > 0 && (
                      <span className="text-muted-foreground">/month</span>
                    )}
                  </div>
                  <CardDescription>{tier.description}</CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  <ul className="space-y-3">
                    {tier.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-2">
                        <Check className="h-5 w-5 text-primary shrink-0 mt-0.5" />
                        <span className="text-sm">{feature}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>

                <CardFooter className="flex flex-col gap-2">
                  {tier.id === 'free' ? (
                    <Button
                      variant="outline"
                      className="w-full"
                      disabled
                    >
                      {isCurrent ? 'Current Plan' : 'Free Forever'}
                    </Button>
                  ) : isCurrent ? (
                    <Button
                      variant="destructive"
                      className="w-full"
                      onClick={handleCancelSubscription}
                      disabled={loading === 'cancel'}
                    >
                      {loading === 'cancel' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      Cancel Subscription
                    </Button>
                  ) : canUpgrade ? (
                    <Button
                      variant={tier.highlighted ? 'default' : 'outline'}
                      className="w-full"
                      onClick={() => {
                        if (getCurrentTier() === 'free') {
                          handleSubscribe(tier.id as 'basic' | 'pro');
                        } else {
                          handleUpgrade(tier.id as 'basic' | 'pro');
                        }
                      }}
                      disabled={loading === tier.id}
                    >
                      {loading === tier.id && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                      {getCurrentTier() === 'free' ? 'Subscribe' : 'Upgrade'}
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      className="w-full"
                      disabled
                    >
                      Not Available
                    </Button>
                  )}
                  
                  {tier.id !== 'free' && (
                    <p className="text-xs text-center text-muted-foreground">
                      Powered by PayPal • Cancel anytime
                    </p>
                  )}
                </CardFooter>
              </Card>
            );
          })}
        </div>

        {/* FAQ or Additional Info */}
        <div className="max-w-4xl mx-auto mt-16 text-center">
          <p className="text-muted-foreground">
            All plans include our core features. Need help choosing?{' '}
            <Button
              variant="link"
              className="p-0 h-auto"
              onClick={() => navigate('/dashboard')}
            >
              Go back to Dashboard
            </Button>
          </p>
        </div>
      </div>
    </div>
  );
}