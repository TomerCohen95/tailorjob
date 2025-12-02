import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Navigation } from '@/components/layout/Navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { supabase } from '@/integrations/supabase/client';
import { CreditCard, Upload, Target, FileText, TrendingUp, AlertCircle } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

interface Subscription {
  tier: 'free' | 'basic' | 'pro';
  status: 'active' | 'cancelled' | 'expired';
  current_period_end?: string;
  paypal_subscription_id?: string;
}

interface Usage {
  user_id: string;
  tier: 'free' | 'basic' | 'pro';
  cv_uploads: number;
  cv_limit: number;
  job_matches: number;
  match_limit: number;
  tailored_cvs: number;
  tailor_limit: number;
  period_start: string;
  period_end: string;
}

export default function Account() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);

  useEffect(() => {
    checkAuth();
    handlePayPalReturn();
    loadAccountData();
  }, []);

  const handlePayPalReturn = async () => {
    // Check if we're returning from PayPal
    const params = new URLSearchParams(window.location.search);
    const subscriptionId = params.get('subscription_id');
    const token = params.get('token');
    
    if (subscriptionId || token) {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) return;

        const API_BASE_URL = import.meta.env.PROD
          ? 'https://tailorjob-api.onrender.com/api'
          : 'http://localhost:8000/api';

        // Extract subscription ID from token or use subscription_id parameter
        const subId = subscriptionId || token;

        toast({
          title: 'Processing subscription...',
          description: 'Please wait while we activate your subscription',
        });

        const response = await fetch(`${API_BASE_URL}/payments/subscriptions/activate`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ subscription_id: subId }),
        });

        if (response.ok) {
          toast({
            title: 'Subscription Activated!',
            description: 'Your subscription is now active. Enjoy your premium features!',
          });
          
          // Clear URL parameters
          window.history.replaceState({}, document.title, window.location.pathname);
          
          // Reload data to show new subscription
          setTimeout(() => loadAccountData(), 1000);
        } else {
          const error = await response.json();
          throw new Error(error.detail || 'Failed to activate subscription');
        }
      } catch (error) {
        console.error('Subscription activation error:', error);
        toast({
          title: 'Activation Error',
          description: error instanceof Error ? error.message : 'Failed to activate subscription',
          variant: 'destructive',
        });
      }
    }
  };

  const checkAuth = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
      navigate('/login');
    }
  };

  const loadAccountData = async () => {
    try {
      setLoading(true);

      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        navigate('/login');
        return;
      }

      const API_BASE_URL = import.meta.env.PROD
        ? 'https://tailorjob-api.onrender.com/api'
        : 'http://localhost:8000/api';

      // Fetch subscription info
      try {
        const subResponse = await fetch(`${API_BASE_URL}/payments/subscriptions/me`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          }
        });

        if (subResponse.ok) {
          const subData = await subResponse.json();
          setSubscription(subData);
        } else if (subResponse.status === 404 || subResponse.status === 422) {
          // No subscription yet - user is on free tier
          setSubscription({
            tier: 'free',
            status: 'active'
          });
        }
      } catch (error) {
        console.log('Subscription API not available, defaulting to free tier');
        setSubscription({
          tier: 'free',
          status: 'active'
        });
      }

      // Fetch usage info
      try {
        const usageResponse = await fetch(`${API_BASE_URL}/payments/usage`, {
          headers: {
            'Authorization': `Bearer ${session.access_token}`,
            'Content-Type': 'application/json',
          }
        });

        if (usageResponse.ok) {
          const usageData = await usageResponse.json();
          setUsage(usageData);
        } else {
          // Default usage for free tier
          setUsage({
            user_id: session.user.id,
            tier: 'free',
            cv_uploads: 0,
            cv_limit: 3,
            job_matches: 0,
            match_limit: 5,
            tailored_cvs: 0,
            tailor_limit: 0,
            period_start: new Date().toISOString(),
            period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
          });
        }
      } catch (error) {
        console.log('Usage API not available, using defaults');
        const { data: { session: currentSession } } = await supabase.auth.getSession();
        setUsage({
          user_id: currentSession?.user?.id || '',
          tier: 'free',
          cv_uploads: 0,
          cv_limit: 3,
          job_matches: 0,
          match_limit: 5,
          tailored_cvs: 0,
          tailor_limit: 0,
          period_start: new Date().toISOString(),
          period_end: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
        });
      }
    } catch (error: any) {
      console.error('Error loading account data:', error);
      toast({
        title: "Error loading account",
        description: error.message || "Could not load subscription information",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const getTierDetails = (tier: string) => {
    switch (tier) {
      case 'pro':
        return {
          name: 'Pro',
          price: '$19.99/month',
          color: 'bg-gradient-to-r from-purple-600 to-blue-600',
          features: ['Unlimited CV uploads', 'Unlimited job matches', 'Unlimited tailored CVs', 'Premium matching algorithm', '24/7 priority support']
        };
      case 'basic':
        return {
          name: 'Basic',
          price: '$9.99/month',
          color: 'bg-gradient-to-r from-blue-600 to-cyan-600',
          features: ['10 CV uploads', '50 job matches/month', '5 tailored CVs/month', 'Advanced matching algorithm', 'Priority email support']
        };
      default:
        return {
          name: 'Free',
          price: '$0',
          color: 'bg-gradient-to-r from-gray-600 to-gray-800',
          features: ['3 CV uploads', '5 job matches/month', 'Basic matching algorithm', 'Email support']
        };
    }
  };

  const calculatePercentage = (used: number, limit: number) => {
    if (limit === -1) return 0; // Unlimited
    return Math.min((used / limit) * 100, 100);
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navigation />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading account information...</p>
          </div>
        </div>
      </div>
    );
  }

  const tier = subscription?.tier || 'free';
  const tierDetails = getTierDetails(tier);

  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Account & Subscription</h1>
          <p className="text-muted-foreground">Manage your subscription and track your usage</p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {/* Current Plan */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5" />
                Current Plan
              </CardTitle>
              <CardDescription>Your subscription details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className={`p-6 rounded-lg ${tierDetails.color} text-white`}>
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-2xl font-bold">{tierDetails.name}</h3>
                  <Badge variant="secondary" className="bg-white/20 text-white hover:bg-white/30">
                    {subscription?.status || 'active'}
                  </Badge>
                </div>
                <p className="text-3xl font-bold mb-4">{tierDetails.price}</p>
                <ul className="space-y-2 text-sm">
                  {tierDetails.features.map((feature, index) => (
                    <li key={index} className="flex items-start gap-2">
                      <span className="text-white/80">✓</span>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {subscription?.current_period_end && (
                <div className="text-sm text-muted-foreground">
                  <p>Next billing date: {formatDate(subscription.current_period_end)}</p>
                </div>
              )}

              <Separator />

              <div className="flex gap-2">
                {tier === 'free' && (
                  <Button 
                    className="w-full" 
                    onClick={() => navigate('/pricing')}
                  >
                    <TrendingUp className="mr-2 h-4 w-4" />
                    Upgrade Plan
                  </Button>
                )}
                {tier === 'basic' && (
                  <>
                    <Button 
                      className="flex-1" 
                      onClick={() => navigate('/pricing')}
                    >
                      <TrendingUp className="mr-2 h-4 w-4" />
                      Upgrade to Pro
                    </Button>
                    <Button 
                      variant="outline" 
                      className="flex-1"
                      onClick={() => {/* Handle cancel */}}
                    >
                      Cancel Plan
                    </Button>
                  </>
                )}
                {tier === 'pro' && (
                  <Button 
                    variant="outline" 
                    className="w-full"
                    onClick={() => {/* Handle cancel */}}
                  >
                    Cancel Subscription
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Usage Statistics */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Usage This Period
              </CardTitle>
              <CardDescription>
                {usage && `${formatDate(usage.period_start)} - ${formatDate(usage.period_end)}`}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* CV Uploads */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Upload className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">CV Uploads</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {usage?.cv_uploads || 0} / {usage?.cv_limit === -1 ? '∞' : usage?.cv_limit || 0}
                  </span>
                </div>
                <Progress
                  value={usage ? calculatePercentage(usage.cv_uploads, usage.cv_limit) : 0}
                  className="h-2"
                />
                {usage && usage.cv_limit !== -1 && usage.cv_limit > 0 && usage.cv_uploads >= usage.cv_limit && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Limit reached - upgrade to continue
                  </p>
                )}
              </div>

              {/* Job Matches */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">Job Matches</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {usage?.job_matches || 0} / {usage?.match_limit === -1 ? '∞' : usage?.match_limit || 0}
                  </span>
                </div>
                <Progress
                  value={usage ? calculatePercentage(usage.job_matches, usage.match_limit) : 0}
                  className="h-2"
                />
                {usage && usage.match_limit !== -1 && usage.match_limit > 0 && usage.job_matches >= usage.match_limit && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Limit reached - upgrade to continue
                  </p>
                )}
              </div>

              {/* Tailored CVs */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">Tailored CVs</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {usage?.tailored_cvs || 0} / {usage?.tailor_limit === -1 ? '∞' : usage?.tailor_limit || 0}
                  </span>
                </div>
                <Progress
                  value={usage ? calculatePercentage(usage.tailored_cvs, usage.tailor_limit) : 0}
                  className="h-2"
                />
                {usage && usage.tailor_limit !== -1 && usage.tailor_limit > 0 && usage.tailored_cvs >= usage.tailor_limit && (
                  <p className="text-xs text-destructive flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    Limit reached - upgrade to continue
                  </p>
                )}
                {usage && usage.tailor_limit === 0 && (
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    Not available in Free tier - upgrade to access
                  </p>
                )}
              </div>

              <Separator />

              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm text-muted-foreground">
                  {tier === 'pro' 
                    ? '🎉 You have unlimited access to all features!'
                    : tier === 'basic'
                    ? 'Upgrade to Pro for unlimited access to all features.'
                    : 'Upgrade to a paid plan to increase your limits and unlock premium features.'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Upgrade Banner */}
        {tier !== 'pro' && (
          <Card className="mt-6 border-primary">
            <CardContent className="p-6">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-primary/10 rounded-lg">
                  <TrendingUp className="h-6 w-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-lg mb-1">
                    {tier === 'free' ? 'Unlock Premium Features' : 'Upgrade to Pro'}
                  </h3>
                  <p className="text-muted-foreground mb-4">
                    {tier === 'free' 
                      ? 'Get more CV uploads, job matches, and advanced matching algorithms with a paid plan.'
                      : 'Get unlimited everything plus premium matching and 24/7 support with Pro.'
                    }
                  </p>
                  <Button onClick={() => navigate('/pricing')}>
                    View Plans
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}