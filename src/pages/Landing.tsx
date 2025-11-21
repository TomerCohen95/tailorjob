import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { FileText, Sparkles, Zap, Target, ArrowRight } from 'lucide-react';

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-primary-light/20 to-background">
      {/* Navigation */}
      <nav className="container mx-auto px-4 py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-accent shadow-glow">
              <FileText className="h-6 w-6 text-primary-foreground" />
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              TailorJob.ai
            </span>
          </div>
          <div className="flex gap-3">
            <Link to="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link to="/signup">
              <Button className="bg-gradient-to-r from-primary to-accent hover:opacity-90">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-4xl mx-auto animate-fade-in">
          <div className="inline-flex items-center gap-2 bg-primary-light text-primary px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Sparkles className="h-4 w-4" />
            AI-Powered CV Tailoring
          </div>
          
          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent leading-tight">
            Tailor your CV for every job — instantly
          </h1>
          
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Upload your CV, paste any job description, and let AI create a perfectly tailored resume that highlights your most relevant experience.
          </p>
          
          <div className="flex gap-4 justify-center flex-wrap">
            <Link to="/signup">
              <Button size="lg" className="bg-gradient-to-r from-primary to-accent hover:opacity-90 text-lg px-8 shadow-glow">
                Start Tailoring Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-8">
              Watch Demo
            </Button>
          </div>
        </div>

        {/* Screenshot Placeholder */}
        <div className="mt-16 max-w-6xl mx-auto">
          <div className="rounded-xl border border-border bg-card shadow-2xl p-8 animate-fade-in">
            <div className="aspect-video bg-gradient-to-br from-primary-light via-accent-light to-primary-light rounded-lg flex items-center justify-center">
              <div className="text-center">
                <FileText className="h-20 w-20 text-primary mx-auto mb-4" />
                <p className="text-lg text-muted-foreground">Product Screenshot</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="container mx-auto px-4 py-20">
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <div className="text-center p-6 rounded-xl bg-card border border-border hover:shadow-lg transition-shadow">
            <div className="inline-flex p-4 rounded-xl bg-primary-light mb-4">
              <Zap className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-foreground">Lightning Fast</h3>
            <p className="text-muted-foreground">
              Generate tailored CVs in seconds, not hours. Our AI understands job requirements instantly.
            </p>
          </div>

          <div className="text-center p-6 rounded-xl bg-card border border-border hover:shadow-lg transition-shadow">
            <div className="inline-flex p-4 rounded-xl bg-accent-light mb-4">
              <Target className="h-8 w-8 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-foreground">Perfectly Targeted</h3>
            <p className="text-muted-foreground">
              Match your experience to job requirements with precision. Stand out from other applicants.
            </p>
          </div>

          <div className="text-center p-6 rounded-xl bg-card border border-border hover:shadow-lg transition-shadow">
            <div className="inline-flex p-4 rounded-xl bg-primary-light mb-4">
              <Sparkles className="h-8 w-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-2 text-foreground">AI-Enhanced</h3>
            <p className="text-muted-foreground">
              Get intelligent suggestions and improvements. Chat with AI to refine your CV further.
            </p>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center bg-gradient-to-r from-primary to-accent rounded-2xl p-12 text-primary-foreground shadow-glow">
          <h2 className="text-4xl font-bold mb-4">Ready to land your dream job?</h2>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of job seekers who've improved their application success rate
          </p>
          <Link to="/signup">
            <Button size="lg" variant="secondary" className="text-lg px-8">
              Get Started for Free
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p>&copy; 2024 TailorJob.ai. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
