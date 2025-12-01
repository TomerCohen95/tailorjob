import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { AlertTriangle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface UpgradeDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  upgradeInfo?: {
    error?: string;
    message?: string;
    upgrade_to?: 'basic' | 'pro';
  };
}

export function UpgradeDialog({ open, onOpenChange, upgradeInfo }: UpgradeDialogProps) {
  const navigate = useNavigate();

  const getBenefits = (tier: 'basic' | 'pro') => {
    if (tier === 'basic') {
      return [
        '10 CV uploads',
        '50 job matches',
        '5 tailored CVs',
        'Advanced matching algorithm'
      ];
    }
    return [
      'Unlimited CV uploads',
      'Unlimited job matches',
      'Unlimited tailored CVs',
      'Premium matching algorithm',
      'Priority support'
    ];
  };

  const getPrice = (tier: 'basic' | 'pro') => {
    return tier === 'basic' ? '$9.99/month' : '$19.99/month';
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-500" />
            <AlertDialogTitle>Upgrade Required</AlertDialogTitle>
          </div>
          <AlertDialogDescription className="space-y-3">
            <p className="text-foreground font-medium">
              {upgradeInfo?.error || "You've reached your plan limit"}
            </p>
            <p className="text-sm">
              {upgradeInfo?.message || "Upgrade to continue using this feature"}
            </p>
            {upgradeInfo?.upgrade_to && (
              <div className="bg-primary/10 p-3 rounded-lg border border-primary/20">
                <p className="text-sm font-medium text-primary">
                  Upgrade to {upgradeInfo.upgrade_to === 'basic' ? 'Basic' : 'Pro'} ({getPrice(upgradeInfo.upgrade_to)}) to unlock:
                </p>
                <ul className="text-sm mt-2 space-y-1 text-muted-foreground">
                  {getBenefits(upgradeInfo.upgrade_to).map((benefit, i) => (
                    <li key={i}>• {benefit}</li>
                  ))}
                </ul>
              </div>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={() => navigate('/pricing')}>
            View Pricing
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}